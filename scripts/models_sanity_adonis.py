"""Models group: end-to-end sanity check on IQMFakeAdonis (noisy simulator of a Lagrange-like chip).

    python -m scripts.models_sanity_adonis              (from the repo root)
    python -m scripts.models_sanity_adonis --n 600      (faster)

It builds a small dataset ITSELF with four temporary stand-ins for circuits/ and simulation/
(those files are still empty): make_circuit, compile_for, exact_z and counts_to_z. When the
other groups push their code, replace these four functions with theirs; everything from
main() onwards (features, training, metrics) is the real models-group pipeline.

Dataset: random 4-qubit circuits (max 2-qubit gates), measured logical i -> clbit i BEFORE
compiling, compiled for IQMFakeAdonis (opt level 1, seed_transpiler 0), 4000 shots.
CZ group of a circuit = ceil(n_cz / GROUP_WIDTH) * GROUP_WIDTH, e.g. 1..10 CZs -> group 10.
"""
import argparse
import time

import numpy as np
from qiskit import transpile
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info import Statevector
from iqm.qiskit_iqm import IQMFakeAdonis

from mlqem.models.features import dataset_features, feature_names
from mlqem.models.metrics import report, rows_to_circuits
from mlqem.models.train import (flatten, split_by_circuit, train_linear, train_random_forest,
                                train_mlp, grouped_cv, param_grid)

N_QUBITS, SHOTS, GROUP_WIDTH = 4, 4000, 10


def make_circuit(seed):
    depth = 1 + seed % 8                       # spread of depths -> spread of CZ counts
    qc = random_circuit(N_QUBITS, depth, max_operands=2, seed=seed)
    # random_circuit can emit 'id' gates, which crash IQM's transpiler (IQMOptimize1QbDecomposition)
    out = qc.copy_empty_like()
    for inst in qc.data:
        if inst.operation.name != "id":
            out.append(inst)
    return out


def compile_for(qc, backend):
    m = qc.copy(); m.measure_all()             # measurements BEFORE transpiling
    return transpile(m, backend, optimization_level=1, seed_transpiler=0)


def exact_z(qc):
    p = Statevector(qc).probabilities()
    k = np.arange(len(p))
    return np.array([p @ (1 - 2 * ((k >> i) & 1)) for i in range(N_QUBITS)])


def counts_to_z(counts):
    z, tot = np.zeros(N_QUBITS), sum(counts.values())
    for key, v in counts.items():
        key = key.replace(" ", "")
        for i in range(N_QUBITS):
            z[i] += v if key[-1 - i] == "0" else -v
    return z / tot


def main(n_circuits):
    backend = IQMFakeAdonis()
    t = time.time()
    originals, compiled, seeds = [], [], []
    for s in range(n_circuits * 2):
        if len(compiled) == n_circuits:
            break
        qc = make_circuit(s)
        c = compile_for(qc, backend)
        if c.count_ops().get("cz", 0) == 0:    # 0 CZs: nothing to learn about noise
            continue
        originals.append(qc); compiled.append(c); seeds.append(s)
    n_cz = np.array([c.count_ops().get("cz", 0) for c in compiled])
    groups = np.ceil(n_cz / GROUP_WIDTH).astype(int) * GROUP_WIDTH

    exact = np.array([exact_z(qc) for qc in originals])
    result = backend.run(compiled, shots=SHOTS, seed_simulator=1).result()
    noisy = np.array([counts_to_z(result.get_counts(i)) for i in range(len(compiled))])
    print(f"{len(compiled)} circuits, CZs {n_cz.min()}..{n_cz.max()} (median {int(np.median(n_cz))}), "
          f"simulated in {time.time() - t:.0f}s")

    # features: (n_circuits, n_qubits, n_features)
    X = dataset_features(compiled, noisy)
    print(f"features per row: {X.shape[2]}")

    tr, te = split_by_circuit(len(X), test_frac=0.3, strata=groups)
    Xtr, ytr, gtr = flatten(X[tr], exact[tr])
    Xte, _, _ = flatten(X[te], exact[te])

    # hyperparameters: grouped CV on TRAIN circuits only
    grid = param_grid(max_depth=[None, 12], min_samples_leaf=[1, 5], max_features=[1.0, 0.5])
    best, _ = grouped_cv(train_random_forest, Xtr, ytr, gtr, grid)
    print(f"RF params chosen by grouped CV: {best}\n")

    models = {"lr": train_linear(Xtr, ytr),
              "rf": train_random_forest(Xtr, ytr, **best),
              "mlp": train_mlp(Xtr, ytr)}
    preds = {name: np.clip(rows_to_circuits(m.predict(Xte), N_QUBITS), -1, 1)
             for name, m in models.items()}
    report(exact[te], groups=groups[te], no_mitigation=noisy[te], **preds)

    imp = models["rf"].feature_importances_
    names = feature_names(N_QUBITS)
    top = np.argsort(imp)[::-1][:8]
    print("\nRF top features: " + ", ".join(f"{names[i]} {imp[i]:.2f}" for i in top))
    print(f"shot-noise floor (4 qubits, {SHOTS} shots): about {np.sqrt(N_QUBITS / SHOTS):.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1500, help="number of circuits")
    main(ap.parse_args().n)
