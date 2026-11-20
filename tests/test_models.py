"""Run from the repo root with:  python -m pytest -q tests"""
import numpy as np
import pytest
from qiskit import QuantumCircuit, transpile
from iqm.qiskit_iqm import IQMFakeAdonis

from mlqem.models.features import (circuit_features, feature_names, fold_angle, measured_qubits,
                                   N_BINS, N_PHYSICAL)
from mlqem.models.metrics import l2_error, bootstrap_ci, rows_to_circuits, error_by_group
from mlqem.models.train import (flatten, split_by_circuit, train_random_forest, train_linear,
                                train_mlp, grouped_cv, param_grid)

SEED = 0
BACKEND = IQMFakeAdonis()   # same star topology and native gates as Lagrange


def fake_data(n_circuits=1000, n_qubits=4, seed=SEED):
    """ideal ~ U[-1,1]; noisy = ideal*0.95**n_cz + N(0,0.02); features = [noisy_i, n_cz]."""
    rng = np.random.default_rng(seed)
    ideal = rng.uniform(-1, 1, (n_circuits, n_qubits))
    n_cz = rng.integers(1, 60, n_circuits)
    noisy = ideal * 0.95 ** n_cz[:, None] + rng.normal(0, 0.02, ideal.shape)
    X = np.stack([noisy, np.repeat(n_cz[:, None], n_qubits, 1)], axis=2)
    return X, ideal, noisy


def compile_adonis(qc):
    """Same convention as circuits/compile.py: measure logical i -> clbit i BEFORE transpiling."""
    qc = qc.copy(); qc.measure_all()
    return transpile(qc, BACKEND, optimization_level=1, seed_transpiler=0)


def make_compiled(seed=0):
    rng = np.random.default_rng(seed)
    qc = QuantumCircuit(4)
    for _ in range(3):
        for q in range(4):
            qc.rx(rng.uniform(-3, 3), q)
        qc.cx(0, 1); qc.cx(2, 3); qc.cx(1, 2)   # 2-3 and 0-1 can't both sit on the star: SWAPs
    return compile_adonis(qc)


# ---------------------------------------------------------------- features
def test_shape_and_columns():
    F = circuit_features(make_compiled(), [0.1, 0.2, 0.3, 0.4])
    assert F.shape == (4, len(feature_names(4)))

def test_same_columns_for_different_circuits():
    a = circuit_features(make_compiled(0), [0] * 4)
    b = circuit_features(make_compiled(1), [0] * 4)
    assert a.shape == b.shape

def test_noisy_value_and_onehot():
    F = circuit_features(make_compiled(), [0.1, 0.2, 0.3, 0.4])
    assert np.allclose(F[:, 0], [0.1, 0.2, 0.3, 0.4])
    assert np.allclose(F[:, 1:5], np.eye(4))

def test_physical_onehot_matches_measurements():
    c = make_compiled()
    F = circuit_features(c, [0] * 4)
    names = feature_names(4)
    cols = [names.index(f"on_phys_{k}") for k in range(N_PHYSICAL)]
    assert np.allclose(F[:, cols].sum(axis=1), 1)
    assert list(F[:, cols].argmax(axis=1)) == measured_qubits(c, 4)

def test_measured_qubit_is_where_the_logical_qubit_really_is():
    # Physical check: put a 50% readout error on ONE physical qubit k. The logical qubit whose noisy
    # <Z> collapses to ~0 must be the one the features place on k.
    # compiled.find_bit(q).index gets this wrong on IQM backends (see features.py docstring).
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError
    qc = QuantumCircuit(4); qc.x(2); qc.cx(0, 1); qc.cx(2, 3); qc.cx(1, 2)   # ideal <Z> = [1,1,-1,-1]
    c = compile_adonis(qc)
    k = measured_qubits(c, 4)[2]
    meas2 = next(i for i in c.data if i.operation.name == "measure" and c.find_bit(i.clbits[0]).index == 2)
    assert c.find_bit(meas2.qubits[0]).index != k                # find_bit would point at the wrong qubit
    noise = NoiseModel(); noise.add_readout_error(ReadoutError([[0.5, 0.5], [0.5, 0.5]]), [k])
    counts = AerSimulator(noise_model=noise).run(c, shots=4000, seed_simulator=0).result().get_counts()
    z = np.array([sum(v * (1 if key.replace(" ", "")[-1 - i] == "0" else -1)
                      for key, v in counts.items()) for i in range(4)]) / 4000
    assert abs(z[2]) < 0.1 and np.allclose(np.delete(z, 2), [1, 1, -1])
    F = circuit_features(c, z)
    assert F[2, feature_names(4).index(f"on_phys_{k}")] == 1

def test_local_cz_sums_to_twice_total():
    # every CZ touches 2 qubits; the 5th (unused) qubit can also take CZs, through SWAPs
    from mlqem.models.features import physical_index_map
    c = make_compiled()
    F = circuit_features(c, [0] * 4)
    names = feature_names(4)
    loc, tot = names.index("local_cz"), names.index("total_cz")
    pm, used = physical_index_map(c), set(measured_qubits(c, 4))
    ancilla_cz = sum(1 for i in c.data if i.operation.name == "cz" for q in i.qubits if pm[q] not in used)
    assert F[:, loc].sum() + ancilla_cz == 2 * F[0, tot]

def test_every_cz_is_on_a_star_edge():
    # with the correct physical indices every CZ touches the centre (physical qubit 2) of the star;
    # with find_bit indices this fails, which is how wrong local_cz values would look
    from mlqem.models.features import physical_index_map
    c = make_compiled()
    pm = physical_index_map(c)
    pairs = [tuple(pm[q] for q in i.qubits) for i in c.data if i.operation.name == "cz"]
    assert pairs and all(2 in p for p in pairs)


def test_lightcone():
    # qubits 2 and 3 never interact with anything: their light cone has no CZ
    qc = QuantumCircuit(4)
    qc.rx(0.3, 2); qc.ry(0.7, 3); qc.h(0); qc.cx(0, 1); qc.cx(1, 0)
    c = compile_adonis(qc)
    F = circuit_features(c, [0] * 4)
    names = feature_names(4)
    lc = F[:, names.index("lightcone_cz")]
    assert lc[2] == 0 and lc[3] == 0 and lc[0] > 0 and lc[1] > 0
    assert np.all(lc <= F[:, names.index("total_cz")])

def test_histogram_counts_all_r_gates():
    c = make_compiled()
    n_r = sum(1 for i in c.data if i.operation.name == "r")
    F = circuit_features(c, [0] * 4)
    assert F[0, -N_BINS:].sum() == n_r

def test_unknown_gate_raises():
    qc = QuantumCircuit(2, 2); qc.h(0); qc.measure([0, 1], [0, 1])   # 'h' is not native
    with pytest.raises(ValueError):
        circuit_features(qc, [0, 0])

def test_fold_angle():
    assert np.isclose(fold_angle(-1.0), 1.0)
    assert np.isclose(fold_angle(2 * np.pi + 0.5), 0.5)
    assert fold_angle(np.array([-3.0, 3.0, 0.0])).max() <= np.pi


# ---------------------------------------------------------------- metrics
def test_l2_known_value():
    assert np.isclose(l2_error(np.array([[3., 0.]]), np.array([[0., 4.]]))[0], 5.0)

def test_l2_zero_when_equal():
    x = np.random.default_rng(0).random((5, 4))
    assert np.allclose(l2_error(x, x), 0)

def test_bootstrap_ci_contains_mean():
    m, lo, hi = bootstrap_ci(np.random.default_rng(0).random(200))
    assert lo <= m <= hi

def test_reshape_order():
    flat = np.arange(8)
    assert np.array_equal(rows_to_circuits(flat, 4), [[0, 1, 2, 3], [4, 5, 6, 7]])

def test_error_by_group():
    pred, exact = np.zeros((4, 2)), np.array([[1, 0], [1, 0], [3, 4], [3, 4]])
    out = error_by_group(pred, exact, [2, 2, 4, 4])
    assert np.isclose(out[2][0], 1) and np.isclose(out[4][0], 5) and out[4][3] == 2


# ---------------------------------------------------------------- training
def test_split_is_disjoint_and_complete():
    tr, te = split_by_circuit(100)
    assert set(tr).isdisjoint(te) and len(tr) + len(te) == 100

def test_stratified_split_covers_every_group():
    strata = np.repeat([2, 4, 6, 8], 25)
    tr, te = split_by_circuit(100, strata=strata)
    assert set(tr).isdisjoint(te) and len(tr) + len(te) == 100
    assert all((strata[te] == g).sum() == 8 for g in [2, 4, 6, 8])   # round(0.3*25) = 8

def test_flatten_keeps_circuit_rows_together():
    X, y, _ = fake_data(10)
    Xf, yf, g = flatten(X, y)
    assert Xf.shape[0] == 40 and list(g[:4]) == [0, 0, 0, 0]
    assert np.allclose(yf[:4], y[0])

@pytest.mark.parametrize("train_fn", [train_random_forest, train_mlp])
def test_model_beats_no_mitigation_on_fake_data(train_fn):
    X, ideal, noisy = fake_data(800)
    tr, te = split_by_circuit(len(X))
    Xtr, ytr, _ = flatten(X[tr], ideal[tr]); Xte, _, _ = flatten(X[te], ideal[te])
    model = train_fn(Xtr, ytr)
    err = l2_error(rows_to_circuits(model.predict(Xte), 4), ideal[te]).mean()
    err_raw = l2_error(noisy[te], ideal[te]).mean()
    assert err < 0.6 * err_raw

def test_grouped_cv_returns_a_grid_point():
    X, ideal, _ = fake_data(100)
    Xf, yf, g = flatten(X, ideal)
    grid = param_grid(min_samples_leaf=[1, 20])
    best, scores = grouped_cv(train_random_forest, Xf, yf, g, grid, n_splits=3)
    assert best in grid and len(scores) == 2

def test_reproducible():
    X, ideal, _ = fake_data(200)
    Xf, yf, _ = flatten(X, ideal)
    for fn in (train_random_forest, train_mlp):
        assert np.allclose(fn(Xf, yf).predict(Xf), fn(Xf, yf).predict(Xf))
