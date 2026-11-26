# Next steps

## 1. Run the pipeline (everyone)

```
git switch main
git pull
python -m scripts.run_models
```

This trains LR, RF and MLP on `data/sim_test`, the shared test dataset (1200 circuits on the fake Lagrange, 200 per CZ group), and prints the error of each model next to "no mitigation", overall and per CZ group. Takes ~10 s.

To make your own dataset (~1 min):

```
python -m scripts.build_dataset                  # saved in data/run_001, then run_002, ...
python -m scripts.build_dataset --per-group 20   # small and quick
python -m scripts.run_models --name run_001      # train on it
```

Every run goes in a new numbered folder, nothing is overwritten. Your runs stay on your PC (they're git-ignored); only `data/sim_test` is in the repo.

**About the seed:** the fake backend ignores `seed_simulator`, so two runs with the same settings give slightly different noisy values. So, to compare two models or two settings, always use the SAME saved dataset (e.g. `sim_test`), never two separate runs.

**About the best possible error:** each noisy value comes from 4000 shots, so it has a statistical error of up to 1/sqrt(4000) = 0.016; over 4 qubits that's an L2 of about 0.03. No method can go much below ~0.03 with 4000 shots (RF is at 0.049 on `sim_test`). More shots lower it: 4x the shots halves it.

To use a dataset in your own code or notebook:

```python
from scripts.build_dataset import load_dataset
table, circuits, compiled = load_dataset("sim_test")   # table: one row per circuit
```

Then go back to your group's branch and bring main into it: `git switch <branch>`, `git merge main`.

## 2. What each group does now

### Circuits & hardware

- `compile.py` now uses `target=backend.target` (see the comment there): compiled circuits are written on the physical qubits, and they survive saving to file.
- Write `mlqem/circuits/hardware.py`: send a LIST of compiled circuits to Lagrange in one job, save raw counts, job id, date and calibration data. Retry if "Slot reserved to another project".
- First real test, ~10 circuits, including some with a known answer (|0000>, X on qubit 1) to check the qubits are where we think. Note how long the queue takes.
- Then: test circuits for generalisation (deeper ones, beyond group 12, and a small Ising Trotter circuit).

### Simulation & ZNE

- The seed: `compute_noisy_z_expectations` takes a `seed`, but IQMFakeAdonis ignores it (same circuits + same seed give different values). Find out if there's a way to make it reproducible (e.g. running the fake backend's noise model directly with Aer); otherwise remove the parameter or say clearly in the docstring that it does nothing, so nobody relies on it.
- Write `mlqem/simulation/zne.py`: fold every CZ into CZ CZ CZ (noise factor 3), run factor 1 and 3, extrapolate `Z(0) = (3 Z(1) - Z(3)) / 2`. Compiled circuits only contain r and cz, so folding by hand is easy, no Mitiq needed.
- Then add ZNE as one more line in the results (talk with the coordinator about adding a `zne_z` column to the dataset).

### Models

- Replace the stand-ins in `scripts/models_sanity_adonis.py` with `load_dataset`, or keep `scripts/run_models.py` as the main one.
- Data efficiency: train on 50, 100, 200, 400, 840 circuits and plot error vs number of training circuits (always on `sim_test`).
- RF uses almost only `noisy_z` (importance 0.99): check whether the other features help at all (train with and without them).
- Generalisation preview: train on groups 2-8, test on 10-12.
