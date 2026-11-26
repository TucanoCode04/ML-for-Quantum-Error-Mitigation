"""Train and evaluate the models on a saved dataset.

    python -m scripts.run_models                  (uses data/sim_test, the shared dataset)
    python -m scripts.run_models --name run_001   (one of your own runs)

Uses only the models group's code: features -> split by circuit (stratified by CZ group)
-> LR, RF, MLP -> L2 error with 95% bootstrap intervals, overall and per CZ group.
"""

import argparse

import numpy as np

from mlqem.models.features import dataset_features, feature_names
from mlqem.models.metrics import report, rows_to_circuits
from mlqem.models.train import flatten, split_by_circuit, train_linear, train_mlp, train_random_forest
from scripts.build_dataset import load_dataset


def main(name):
    table, _, compiled = load_dataset(name)
    exact, noisy = np.stack(table.exact_z), np.stack(table.noisy_z)
    groups = table.group.to_numpy()
    n_qubits = exact.shape[1]

    X = dataset_features(compiled, noisy)
    tr, te = split_by_circuit(len(X), test_frac=0.3, strata=groups)
    Xtr, ytr, _ = flatten(X[tr], exact[tr])
    Xte, _, _ = flatten(X[te], exact[te])
    print(f"{len(table)} circuits: {len(tr)} train, {len(te)} test, {X.shape[2]} features per row\n")

    models = {"lr": train_linear(Xtr, ytr), "rf": train_random_forest(Xtr, ytr), "mlp": train_mlp(Xtr, ytr)}
    preds = {k: np.clip(rows_to_circuits(m.predict(Xte), n_qubits), -1, 1) for k, m in models.items()}
    report(exact[te], groups=groups[te], no_mitigation=noisy[te], **preds)

    imp, names = models["rf"].feature_importances_, feature_names(n_qubits)
    top = np.argsort(imp)[::-1][:6]
    print("\nRF most used features: " + ", ".join(f"{names[i]} {imp[i]:.2f}" for i in top))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="sim_test")
    main(ap.parse_args().name)
