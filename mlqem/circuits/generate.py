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
