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
