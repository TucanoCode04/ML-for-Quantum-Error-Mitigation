"""Build a dataset: circuits -> exact values -> noisy values -> saved to data/.

    python -m scripts.build_dataset                       (200 circuits per group, about 1 min)
    python -m scripts.build_dataset --per-group 20        (quick, small)

WHERE IT IS SAVED
Every run is saved in a NEW numbered folder (data/run_001, data/run_002, ...), never overwriting an
older one. To choose the name yourself:
    python -m scripts.build_dataset --name my_name           -> data/my_name/
If the folder already exists the script stops, nothing is overwritten.

Numbered runs (data/run_*) stay on your PC, they are git-ignored: if everyone pushed their own
run_001, different datasets with the same name would clash on GitHub.
When a run is IMPORTANT and others need it (e.g. data/sim_test, or later the first Lagrange data),
build it with a meaningful --name and commit it on purpose: names that don't start with run_
are not ignored.

This is the glue between the three groups: it only calls their functions in the right order and
saves the result, so nobody has to regenerate circuits every time.

    1. circuits      mlqem.circuits.generate.build_dataset      -> seed, depth, circuit, compiled, n_cz, group
    2. exact values  mlqem.simulation.ideal, on the ORIGINAL circuits
    3. noisy values  mlqem.simulation.noisy, all compiled circuits in one backend.run call
    4. save          data/<name>/
                       circuits.qpy   original circuits (Qiskit's own file format)
                       compiled.qpy   compiled circuits (QPY keeps the layout too)
                       table.parquet  one row per circuit, same order as the two .qpy files

To use a saved dataset:  from scripts.build_dataset import load_dataset
                         table, circuits, compiled = load_dataset("sim_test")

Note: IQMFakeAdonis ignores seed_simulator, so two runs with the same settings give slightly
different noisy values. To compare results, use the same saved dataset.

LATER: on Lagrange step 3 becomes hardware.py (send jobs, save raw counts), then the same
counts -> <Z_i> function. ZNE values will become one more column of the table.
"""

import argparse
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from iqm.qiskit_iqm import IQMFakeAdonis
from qiskit import qpy

from mlqem.circuits.compile import OPT_LEVEL, TRANSPILER_SEED
from mlqem.circuits.generate import build_dataset as build_circuits  # same name as this script, renamed
from mlqem.simulation.ideal import compute_exact_z_expectations
from mlqem.simulation.noisy import compute_noisy_z_expectations

DATA_DIR = Path("data")


def build(per_group=200, n_qubits=4, shots=4000, sim_seed=1):
    """Run the whole pipeline on the fake Lagrange. Returns (table, circuits, compiled)."""
    backend = IQMFakeAdonis()

    t = time.time()
    records = build_circuits(backend, n_qubits=n_qubits, n_per_group=per_group)
    print(f"{len(records)} circuits generated and compiled in {time.time() - t:.0f}s")

    circuits = [r["circuit"] for r in records]
    compiled = [r["compiled"] for r in records]

    exact = np.array([compute_exact_z_expectations(c) for c in circuits])

    t = time.time()
    noisy = compute_noisy_z_expectations(compiled, backend, shots=shots, seed=sim_seed)
    print(f"noisy simulation done in {time.time() - t:.0f}s")

    table = pd.DataFrame({
        "seed": [r["seed"] for r in records],
        "depth": [r["depth"] for r in records],
        "n_qubits": n_qubits,
        "n_cz": [r["n_cz"] for r in records],
        "group": [r["group"] for r in records],
        "exact_z": list(exact),
        "noisy_z": list(noisy),
        "backend": backend.name,
        "shots": shots,
        "sim_seed": sim_seed,
        "transpiler_seed": TRANSPILER_SEED,
        "opt_level": OPT_LEVEL,
        "date": datetime.now().isoformat(timespec="seconds"),
    })
    return table, circuits, compiled


def next_run_name():
    """First free name among run_001, run_002, ..."""
    n = 1
    while (DATA_DIR / f"run_{n:03d}").exists():
        n += 1
    return f"run_{n:03d}"


def save_dataset(name, table, circuits, compiled):
    folder = DATA_DIR / name
    if folder.exists():
        raise FileExistsError(f"{folder} already exists, choose another --name (nothing is overwritten)")
    folder.mkdir(parents=True)
    with open(folder / "circuits.qpy", "wb") as f:
        qpy.dump(circuits, f)
    with open(folder / "compiled.qpy", "wb") as f:
        qpy.dump(compiled, f)
    table.to_parquet(folder / "table.parquet")
    print(f"saved to {folder}/")


def load_dataset(name):
    """Return (table, circuits, compiled). table.exact_z / table.noisy_z hold one array per circuit;
    np.stack(table.exact_z) gives the (n_circuits, n_qubits) matrix."""
    folder = DATA_DIR / name
    table = pd.read_parquet(folder / "table.parquet")
    with open(folder / "circuits.qpy", "rb") as f:
        circuits = qpy.load(f)
    with open(folder / "compiled.qpy", "rb") as f:
        compiled = qpy.load(f)
    return table, circuits, compiled


def summary(table):
    exact, noisy = np.stack(table.exact_z), np.stack(table.noisy_z)
    err = np.linalg.norm(noisy - exact, axis=1)
    print("\nno-mitigation error (mean L2, noisy vs exact) per CZ group:")
    for g, e in pd.Series(err).groupby(table.group.values):
        print(f"  group {g:>2}: {e.mean():.3f}   ({len(e)} circuits)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-group", type=int, default=200, help="circuits per CZ group")
    ap.add_argument("--name", default=None, help="folder name inside data/ (default: next run_XXX)")
    ap.add_argument("--shots", type=int, default=4000)
    args = ap.parse_args()

    name = args.name or next_run_name()
    if (DATA_DIR / name).exists():  # check before spending a minute building it
        raise SystemExit(f"data/{name} already exists, choose another --name (nothing is overwritten)")
    table, circuits, compiled = build(per_group=args.per_group, shots=args.shots)
    save_dataset(name, table, circuits, compiled)
    summary(table)
