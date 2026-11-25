"""Train the models.                                              Group: Models

WHAT THIS FILE SHOULD DO FOR NOW
Train models that map a feature row to the exact <Z_i> of that row. Start with random forest and
linear regression; MLP later, GNN only if there is time.

WHAT NEEDS TO BE IMPLEMENTED (names and details are up to you)
    - Train a random forest regressor.
    - Train a linear regression.
    - A way to split data into train / test.

WHAT THE PAPER DOES
    - Models compared: linear regression (OLS), random forest, MLP, GNN. The random forest was the
      best overall and is cheap to train, so it's our main model. They used 100 trees.
    - Target of each row = the exact <Z_i> of that qubit.

BE CAREFUL WITH
    - Split by CIRCUIT, never by row: the 4 rows of a circuit share most features. If some go in
      train and some in test, the test is leaked and results look better than they are.
    - Fix random_state everywhere so results can be reproduced.
    - Choose hyperparameters on a validation set or with cross-validation, never on the test set.
    - Real data isn't ready yet, so make fake data to start: e.g. ideal values uniform in [-1, 1],
      a random n_cz per circuit, noisy = ideal * 0.95**n_cz + small gaussian noise (0.02), rows =
      [noisy_i, n_cz]. A random forest should clearly beat "no mitigation" there; if it doesn't,
      something is wrong in the code, not in the physics.
"""

import itertools

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 0


def flatten(X, y):
    """X (n_circuits, n_qubits, n_feat), y (n_circuits, n_qubits) -> rows, targets, circuit id per row."""
    n_c, n_q, n_f = X.shape
    groups = np.repeat(np.arange(n_c), n_q)
    return X.reshape(-1, n_f), np.asarray(y).reshape(-1), groups


def split_by_circuit(n_circuits, test_frac=0.3, seed=SEED, strata=None):
    """Return train and test CIRCUIT indices (all rows of a circuit stay together).
    strata (optional, length n_circuits, e.g. CZ group): take test_frac of EACH stratum, so every
    CZ group is represented in the test set."""
    rng = np.random.default_rng(seed)
    if strata is None:
        perm = rng.permutation(n_circuits)
        n_test = int(round(test_frac * n_circuits))
        return np.sort(perm[n_test:]), np.sort(perm[:n_test])
    strata = np.asarray(strata)
    tr, te = [], []
    for s in np.unique(strata):
        idx = rng.permutation(np.flatnonzero(strata == s))
        n_test = int(round(test_frac * len(idx)))
        te.extend(idx[:n_test]); tr.extend(idx[n_test:])
    return np.sort(tr), np.sort(te)


def train_random_forest(X, y, n_estimators=100, **kw):
    return RandomForestRegressor(n_estimators=n_estimators, random_state=SEED, n_jobs=-1, **kw).fit(X, y)


def train_linear(X, y):
    return LinearRegression().fit(X, y)


def train_mlp(X, y, hidden=(64, 64), alpha=1e-4, max_iter=2000, **kw):
    """Small MLP (sklearn is enough at this size). Features are standardised first: counts like
    total_cz are ~10-50 while noisy_z is in [-1, 1], and MLPs train badly on unscaled inputs."""
    mlp = MLPRegressor(hidden_layer_sizes=hidden, alpha=alpha, max_iter=max_iter,
                       early_stopping=True, random_state=SEED, **kw)
    return make_pipeline(StandardScaler(), mlp).fit(X, y)


TRAINERS = {"lr": train_linear, "rf": train_random_forest, "mlp": train_mlp}


def param_grid(**options):
    """param_grid(max_depth=[None, 10], min_samples_leaf=[1, 5]) -> list of dicts (all combinations)."""
    keys = list(options)
    return [dict(zip(keys, vals)) for vals in itertools.product(*options.values())]


def grouped_cv(train_fn, X, y, groups, grid, n_splits=5):
    """Pick hyperparameters by grouped CV on TRAIN rows only. Returns (best_params, {params: mse}).
    Folds never split a circuit. Score = mean squared error per row (= mean L2^2 / n_qubits)."""
    scores = {}
    for params in grid:
        mses = []
        for tr, va in GroupKFold(n_splits).split(X, y, groups):
            m = train_fn(X[tr], y[tr], **params)
            mses.append(np.mean((m.predict(X[va]) - y[va]) ** 2))
        scores[tuple(sorted(params.items()))] = float(np.mean(mses))
    best = min(scores, key=scores.get)
    return dict(best), scores


def cv_score_rf(X, y, groups, param_grid, n_splits=5):
    """Kept for compatibility: grouped CV for the random forest, returns best params."""
    return grouped_cv(train_random_forest, X, y, groups, param_grid, n_splits)[0]

