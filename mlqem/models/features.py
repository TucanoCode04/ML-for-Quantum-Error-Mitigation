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
"""
