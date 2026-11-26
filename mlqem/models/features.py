"""Features: describe a circuit with numbers.                      Group: Models

WHAT THIS FILE SHOULD DO FOR NOW
Turn one circuit (compiled) + its noisy <Z_i> values into rows of numbers a model can read.
With 4 qubits, one circuit gives 4 rows.

WHAT NEEDS TO BE IMPLEMENTED (names and details are up to you)
    - A function: compiled circuit + noisy values (length n_qubits)  ->  array (n_qubits, n_features).

WHAT THE PAPER DOES
    - ONE ROW PER OBSERVABLE (Fig. 7): the model predicts one <Z_i> at a time, and row i says
      which qubit it is about. We tried one row per circuit predicting all 4 values together and
      it was worse than no mitigation at all. One row per qubit worked much better.
    - The features are: the noisy expectation value, counts of the gates in the circuit, and a
      histogram of the rotation angles of the single-qubit gates. For the GNN also the device
      calibration data (T1, T2, gate errors), which we may need later for the drift experiment.

A REASONABLE ROW i (change or add what you want)
    - noisy <Z_i>                         the most important one, it's what the model corrects
    - which qubit it is (one-hot)         different qubits have different noise
    - CZs touching this qubit             local noise
    - total CZs, circuit depth            noise of the whole circuit
    - histogram of rotation angles        see below

BE CAREFUL WITH
    - Angles: on Lagrange single-qubit gates are r(theta, phi); theta is how much it rotates.
      Fold theta into [0, pi] (a rotation by -theta is as "big" as one by theta), e.g.
      abs((theta + pi) % (2*pi) - pi). Then np.histogram with a FIXED range=(0, pi) and a fixed
      number of bins: if the bin edges change between circuits the columns don't mean the same thing.
    - Physical vs logical: in the compiled circuit gates act on PHYSICAL qubits
      (compiled.find_bit(q).index), while the noisy values are indexed by LOGICAL qubit.
      compiled.layout.final_index_layout()[i] is the physical qubit of logical qubit i.
    - Every circuit must give the same number of columns in the same order.
    - Loop over compiled.data: every item has .operation.name, .operation.params, .qubits.
    
    - Physical vs logical: DON'T use compiled.find_bit(q).index as the physical qubit. On IQM
      backends it's wrong after transpiling (wrong in 200/200 test circuits). Use
      physical_index_map(compiled), which follows the same rule IQM uses when it sends the job
      to Lagrange. The noisy values are indexed by LOGICAL qubit;
      compiled.layout.final_index_layout()[i] is the physical qubit of logical qubit i (this one is correct).
"""

import numpy as np
from qiskit.converters import circuit_to_dag
from qiskit.transpiler.passes import RemoveBarriers

N_BINS = 8                  # fixed number of angle bins
ANGLE_RANGE = (0.0, np.pi)  # fixed range, so columns mean the same in every circuit
N_PHYSICAL = 5              # qubits on Lagrange / IQMFakeAdonis
TWO_QUBIT = {"cz"}
ONE_QUBIT = {"r", "id"}
IGNORE = {"barrier", "measure", "delay"}


def feature_names(n_qubits, n_physical=N_PHYSICAL):
    """Column names, in the exact order produced by circuit_features."""
    edges = np.linspace(*ANGLE_RANGE, N_BINS + 1)
    return (["noisy_z"]
            + [f"is_qubit_{i}" for i in range(n_qubits)]
            + [f"on_phys_{k}" for k in range(n_physical)]
            + ["local_cz", "lightcone_cz", "lightcone_1q",
               "total_cz", "depth", "cz_depth", "n_1q_gates"]
            + [f"angle_{edges[b]:.2f}_{edges[b+1]:.2f}" for b in range(N_BINS)])


def fold_angle(theta):
    """Fold into [0, pi]: rotating by -theta is as 'big' as rotating by theta."""
    return np.abs((np.asarray(theta, dtype=float) + np.pi) % (2 * np.pi) - np.pi)


def physical_index_map(compiled):
    """{qubit object: physical qubit index}, with the same rule IQM uses when it sends the circuit
    to the hardware: initial_layout if the circuit is still expressed with the virtual registers
    (always the case after IQM's transpiler), otherwise find_bit."""
    lay = compiled.layout
    if lay is not None and lay.initial_layout.get_registers() == set(compiled.qregs):
        return {q: p for p, q in lay.initial_layout.get_physical_bits().items()}
    return {q: compiled.find_bit(q).index for q in compiled.qubits}


def measured_qubits(compiled, n_qubits, phys_map=None):
    """Physical qubit measured into clbit i, for i = 0..n_qubits-1 (= physical qubit of logical i,
    because measurements are added before transpiling, see circuits/compile.py)."""
    phys_map = physical_index_map(compiled) if phys_map is None else phys_map
    phys = {}
    for inst in compiled.data:
        if inst.operation.name == "measure":
            phys[compiled.find_bit(inst.clbits[0]).index] = phys_map[inst.qubits[0]]
    if not phys:
        raise ValueError("compiled circuit has no measurements (add them before transpiling)")
    missing = [i for i in range(n_qubits) if i not in phys]
    if missing:
        raise ValueError(f"no measurement writes clbit(s) {missing}")
    out = [phys[i] for i in range(n_qubits)]
    if compiled.layout is not None:   # cross-check with the transpiler's own bookkeeping
        fin = list(compiled.layout.final_index_layout())[:n_qubits]
        if fin != out:
            raise RuntimeError(f"measured qubits {out} != final_index_layout {fin}")
    return out


def _lightcone_counts(compiled, n_qubits):
    """For each clbit i: (#CZ, #1q gates) in the backward light cone of its measurement."""
    dag = RemoveBarriers()(compiled) if any(i.operation.name == "barrier" for i in compiled.data) else compiled
    dag = circuit_to_dag(dag)
    out = {}
    for node in dag.op_nodes():
        if node.op.name != "measure":
            continue
        i = dag.find_bit(node.cargs[0]).index
        n_cz = n_1q = 0
        for anc in dag.ancestors(node):
            name = getattr(getattr(anc, "op", None), "name", None)
            if name in TWO_QUBIT:
                n_cz += 1
            elif name in ONE_QUBIT:
                n_1q += 1
        out[i] = (n_cz, n_1q)
    return [out.get(i, (np.nan, np.nan)) for i in range(n_qubits)]


def circuit_features(compiled, noisy_z, n_physical=N_PHYSICAL):
    """compiled: transpiled QuantumCircuit (with measurements, logical i -> clbit i).
    noisy_z: length n_qubits, LOGICAL order. Returns array (n_qubits, n_features)."""
    noisy_z = np.asarray(noisy_z, dtype=float)
    n_qubits = len(noisy_z)
    if compiled.num_qubits > n_physical:
        raise ValueError(f"circuit has {compiled.num_qubits} qubits but n_physical={n_physical}")

    phys_map = physical_index_map(compiled)
    phys_of_logical = measured_qubits(compiled, n_qubits, phys_map)

    cz_per_phys, angles, n_1q, n_cz = {}, [], 0, 0
    for inst in compiled.data:
        name = inst.operation.name
        if name in IGNORE:
            continue
        phys = [phys_map[q] for q in inst.qubits]
        if name in TWO_QUBIT:
            n_cz += 1
            for p in phys:
                cz_per_phys[p] = cz_per_phys.get(p, 0) + 1
        elif name in ONE_QUBIT:
            n_1q += 1
            if name == "r":                       # r(theta, phi): theta = rotation size
                angles.append(float(inst.operation.params[0]))
        else:
            # fail loudly: an unknown gate means the circuit wasn't compiled to native gates
            raise ValueError(f"unexpected gate '{name}' in compiled circuit")

    hist, _ = np.histogram(fold_angle(angles), bins=N_BINS, range=ANGLE_RANGE)
    cz_depth = compiled.depth(lambda i: i.operation.name in TWO_QUBIT)
    depth = compiled.depth(lambda i: i.operation.name not in IGNORE)
    shared = [n_cz, depth, cz_depth, n_1q]
    lightcone = _lightcone_counts(compiled, n_qubits)

    rows = []
    for i in range(n_qubits):
        onehot = np.zeros(n_qubits); onehot[i] = 1.0
        p = phys_of_logical[i]
        phys_onehot = np.zeros(n_physical); phys_onehot[p] = 1.0
        rows.append(np.concatenate([[noisy_z[i]], onehot, phys_onehot,
                                    [cz_per_phys.get(p, 0), *lightcone[i]], shared, hist]))
    return np.array(rows)


def dataset_features(compiled_circuits, noisy_values, n_physical=N_PHYSICAL):
    """Many circuits -> X of shape (n_circuits, n_qubits, n_features), ready for train.flatten."""
    return np.stack([circuit_features(c, z, n_physical) for c, z in zip(compiled_circuits, noisy_values)])
