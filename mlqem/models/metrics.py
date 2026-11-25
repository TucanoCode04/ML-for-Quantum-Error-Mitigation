"""Error measure.                                                 Group: Models

WHAT THIS FILE SHOULD DO FOR NOW
Measure how far a set of predictions is from the exact values, the same way the paper does, so
that every method (no mitigation, ZNE, LR, RF, MLP) is compared with the same number.

WHAT NEEDS TO BE IMPLEMENTED (names and details are up to you)
    - L2 error per circuit: predicted and exact are arrays (n_circuits, n_qubits), output is one
      number per circuit.
    - Later: bootstrap confidence intervals of the mean error.

WHAT THE PAPER DOES
    - For each circuit, the L2 distance between the vector of predicted <Z_i> and the vector of
      exact <Z_i>:  sqrt(sum_i (predicted_i - exact_i)^2).  Then the average over test circuits.
    - Results are shown as a function of the number of two-qubit gates (for us: CZ groups), with
      "no mitigation" (noisy vs exact) as the reference line.
    - Bootstrap: resample the test circuits with replacement many times (e.g. 1000), compute the
      mean each time, and take the 2.5 and 97.5 percentiles as the 95% interval.

BE CAREFUL WITH
    - Reshape the row predictions back to (n_circuits, n_qubits) before computing the error,
      keeping the qubits in the right order.
    - The L2 error grows with the number of qubits (about sqrt(n)), so only compare results with
      the same number of qubits.
    - Always report the "no mitigation" error next to the models, otherwise numbers mean nothing.
"""
import numpy as np


def rows_to_circuits(pred_rows, n_qubits):
    """Flat row predictions (n_circuits*n_qubits,) -> (n_circuits, n_qubits).
    Works because train.flatten flattens circuit by circuit, qubit 0..n-1 within each."""
    pred_rows = np.asarray(pred_rows)
    if pred_rows.size % n_qubits:
        raise ValueError(f"{pred_rows.size} rows is not a multiple of n_qubits={n_qubits}")
    return pred_rows.reshape(-1, n_qubits)


def l2_error(predicted, exact):
    """predicted, exact: (n_circuits, n_qubits) -> (n_circuits,)"""
    predicted, exact = np.asarray(predicted, dtype=float), np.asarray(exact, dtype=float)
    assert predicted.shape == exact.shape and predicted.ndim == 2, (predicted.shape, exact.shape)
    return np.sqrt(((predicted - exact) ** 2).sum(axis=1))


def mean_error(predicted, exact):
    return l2_error(predicted, exact).mean()


def bootstrap_ci(errors, n_boot=1000, ci=95, seed=0):
    """Resample circuits with replacement; return (mean, low, high)."""
    errors = np.asarray(errors, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(errors), size=(n_boot, len(errors)))
    means = errors[idx].mean(axis=1)
    a = (100 - ci) / 2
    return errors.mean(), np.percentile(means, a), np.percentile(means, 100 - a)


def error_by_group(predicted, exact, groups, **boot_kw):
    """Mean L2 + CI per CZ group. groups: (n_circuits,) e.g. the CZ group of each test circuit.
    Returns {group: (mean, low, high, n_circuits)} sorted by group."""
    err, groups = l2_error(predicted, exact), np.asarray(groups)
    return {g: (*bootstrap_ci(err[groups == g], **boot_kw), int((groups == g).sum()))
            for g in np.unique(groups)}


def report(exact, groups=None, **methods):
    """Print mean error + 95% CI per method (and per group if given). Returns the numbers.
    Always pass no_mitigation=noisy, e.g. report(exact, no_mitigation=noisy, rf=pred_rf)."""
    if "no_mitigation" not in methods:
        print("WARNING: no 'no_mitigation' reference passed, numbers alone mean nothing")
    out = {}
    for name, pred in methods.items():
        m, lo, hi = bootstrap_ci(l2_error(pred, exact))
        out[name] = {"all": (m, lo, hi)}
        print(f"{name:>15}: {m:.4f}  [{lo:.4f}, {hi:.4f}]")
    if groups is not None:
        print("\nby group (mean L2):")
        print(f"{'group':>6} {'n':>5} " + " ".join(f"{n:>15}" for n in methods))
        per = {name: error_by_group(pred, exact, groups) for name, pred in methods.items()}
        for g in np.unique(groups):
            n = next(iter(per.values()))[g][3]
            print(f"{g:>6} {n:>5} " + " ".join(f"{per[name][g][0]:>15.4f}" for name in methods))
        for name in methods:
            out[name]["by_group"] = per[name]
    return out
