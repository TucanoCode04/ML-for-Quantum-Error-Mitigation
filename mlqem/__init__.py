"""ML-QEM on Lagrange: the shared package of the three groups.

FINAL LAYOUT (files marked "later" don't exist yet, they are here so we know where things will go)

    mlqem/
        circuits/       Circuits & hardware group
            generate.py     random circuits, grouped by number of CZs                    now
            compile.py      compile circuits for Lagrange                                now
            hardware.py     send batches of circuits to Lagrange, save counts + calibration   later
        simulation/     Simulation & ZNE group
            ideal.py        exact <Z_i> of a circuit                                     now
            noisy.py        <Z_i> from measurement counts, running on a backend          now
            zne.py          zero-noise extrapolation, the baseline to beat               later
        models/         Models group
            features.py     circuit + noisy values  ->  feature rows                     now
            train.py        random forest, linear regression (MLP, GNN later)            now
            metrics.py      L2 error, bootstrap confidence intervals                     now
    scripts/        later: short scripts that glue the groups (build the dataset, run an experiment)
    notebooks/      later: exploration and plots
    data/           later: saved datasets (hardware data can't be regenerated, so we keep it)

The code inside each file is up to each group. The only things we must all agree on are below,
because they are where the groups meet.

HOW THE PARTS CONNECT
    - A circuit is identified by its seed (an int).
    - Every vector of <Z> values is a numpy array of length n_qubits where position i is LOGICAL
      qubit i, i.e. qubit i of the original circuit, NOT the physical qubit of the chip where it ended up.
    - The circuits group gives, for every circuit: seed, original circuit (no measurements),
      compiled circuit (with measurements, only Lagrange gates), number of CZs, CZ group.
    - The simulation group uses the original circuit for the exact values and the compiled
      circuit for the noisy values.
    - The models group uses compiled circuit + noisy values to build the features, and the exact
      values as the target to learn.

Import across groups like  `from mlqem.circuits.compile import ...`  and run things from the repo
root with  `python -m ...`  (or a notebook started in the repo root) so that `mlqem` is found.
"""
