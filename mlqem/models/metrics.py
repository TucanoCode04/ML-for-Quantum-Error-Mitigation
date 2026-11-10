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
