"""Random circuits for training and testing.                      Group: Circuits & hardware

WHAT THIS FILE SHOULD DO FOR NOW
Generate many random circuits on n qubits (we start with 4; Lagrange has 5) and sort them by how
many CZ gates they have once compiled for Lagrange. Every row of the final dataset starts from one
of these circuits, so this is the raw material of the whole project.

WHAT NEEDS TO BE IMPLEMENTED (names and details are up to you)
    - Make one random circuit from (number of qubits, depth, seed).
      The same seed must always give the same circuit, so that anyone can rebuild it.
      It must have NO measurements: the simulation group needs it clean for the exact values.
    - Count the CZ gates of a circuit. Use it on the COMPILED circuit: before compiling there are
      CX, SWAP, ... gates that become a different number of CZs.
    - Build a whole set of circuits grouped by CZ count, e.g. groups 2, 4, ..., 12 with N circuits
      each. For every circuit keep: seed, original circuit, compiled circuit, number of CZs, group.
      How you look for circuits that fall in each group (random depths, increasing depths, ...)
      is your choice, but write down how a circuit is assigned to a group
      (e.g. "group g = circuits with g-1 or g CZs").

WHAT THE PAPER DOES
    - The models are trained on random circuits and then tested on circuits never seen, also
      deeper ones and a real algorithm (Trotterized Ising evolution). We do the same at small scale.
    - Results are always shown as a function of the number of two-qubit gates, because those are
      the main source of noise. On Lagrange the only two-qubit gate is CZ, so for us
      "difficulty of a circuit" = number of CZs after compiling. That's why we group by it.

BE CAREFUL WITH
    - qiskit.circuit.random.random_circuit already exists. Use at most 2-qubit gates
      (max_operands=2): 3-qubit gates like Toffoli explode into many CZs.
    - Lagrange is a star: only the centre (physical qubit 2) is connected to the others. A two-qubit
      gate between two outer qubits needs SWAPs, and each SWAP is 3 CZs. So the CZ count after
      compiling is much bigger than the number of 2-qubit gates you put in. Count after compiling.
    - Compiling is random (routing), so fix its seed, otherwise the same circuit can give a
      different CZ count each time.
    - Skip circuits with 0 CZs, they teach the model nothing about noise.
    - For now compile with IQMFakeAdonis (from iqm.qiskit_iqm): same topology and gates as Lagrange,
      and it doesn't use the queue.
"""

# Grouping rule:
# - group g = circuits with g-1 or g CZs after compiling, 0 CZs are discarded
# - default groups: 2, 4, 6, 8, 10, 12
# - depths 1 to 5 are tried one after another (1, 2, 3, 4, 5, 1, 2, ...)
# - a circuit is identified by (n_qubits, depth, seed)

from qiskit.circuit.random import random_circuit
import math
from mlqem.circuits.compile import compile_for_backend, TRANSPILER_SEED


def make_random_circuit(n_qubits, depth, seed):
    """Random circuit with no measurements and no 'id' gates.
    Same (n_qubits, depth, seed) always gives the same circuit.
    'id' gates are removed because the compiler can crash on them."""
    qc= random_circuit(n_qubits, depth=depth,max_operands=2, seed=seed)
    clean=qc.copy_empty_like()
    for gate in qc.data:
        if gate.operation.name!="id":
            clean.append(gate)
    return clean


def count_cz(compiled_c):
    """Number of CZ gates. Use it on the compiled circuit:
    the original circuit has no CZ gates."""
    num_cz=compiled_c.count_ops().get("cz",0)
    return num_cz


def assign_group(num_cz, groups=(2, 4, 6, 8, 10, 12)):
    """Group of a circuit from its number of CZs (after compiling).
    Rule: group g = circuits with g-1 or g CZs. Returns None if the circuit
    fits no group (0 CZs, or more CZs than the largest group): discard it.
    Groups must be even numbers."""

    g=math.ceil(num_cz/2)*2
    if g in groups:
        return g
    else:
        return None


def build_dataset(backend, n_qubits=4, groups=(2, 4, 6, 8, 10, 12),
                  n_per_group=200, depths=range(1, 6),
                  max_tries=10000, start_seed=0):
    """Generate random circuits until every group has n_per_group circuits.
    Same arguments always give the same dataset.

    Returns a list of dicts: seed, depth, n_qubits, circuit (original,
    no measurements), compiled, n_cz, group."""

    counts = {g: 0 for g in groups}
    tries=0
    control=False
    depth_list = list(depths) 
    seed=start_seed
    result=[]

    while tries < max_tries and not control:                     
        depth = depth_list[tries % len(depth_list)]
        qc=make_random_circuit(n_qubits,depth,seed)
        compiled_qc=compile_for_backend(qc,backend,TRANSPILER_SEED)
        num_cz=count_cz(compiled_qc)
        group=assign_group(num_cz, groups)

        if group is not None and counts[group]<n_per_group:
            record={
                "seed": seed,
                "depth": depth,
                "n_qubits": n_qubits,
                "circuit": qc,      
                "compiled": compiled_qc,      
                "n_cz": num_cz,
                "group": group,
            }
            result.append(record)
            counts[group]+=1
        seed+=1
        tries+=1
        control=all(counts[g] >= n_per_group for g in groups)   

    if not control:
        print("Some groups did not fill up.", counts)
    return result
