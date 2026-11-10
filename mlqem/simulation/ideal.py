"""Exact <Z_i> values of a circuit.                               Group: Simulation & ZNE

WHAT THIS FILE SHOULD DO FOR NOW
For a circuit, compute what a perfect quantum computer would give: the vector
[<Z_0>, <Z_1>, ..., <Z_{n-1}>], one number per qubit between -1 and +1. This is the "right answer"
the ML models learn to reach, and the reference for every error we report.

WHAT NEEDS TO BE IMPLEMENTED (names and details are up to you)
    - A function: original circuit (no measurements)  ->  numpy array of n_qubits exact values.

HOW <Z_i> COMES OUT OF THE 2^n PROBABILITIES
    With 4 qubits there are 16 basis states |0000>, ..., |1111>, and the simulation gives one
    probability per state. <Z_i> squeezes them into one number per qubit:
        <Z_i> = P(qubit i is 0) - P(qubit i is 1)
              = (sum of probabilities of the states where qubit i is 0)
              - (sum of probabilities of the states where qubit i is 1)
    Every one of the 16 probabilities is used for every qubit, only with a + or - sign.
    So: +1 means qubit i is surely 0, -1 surely 1, 0 means 50/50.

WHAT THE PAPER DOES
    - The observables are the single-qubit Z expectation values, one per qubit, and every one of
      them becomes a separate training example (see the models group).
    - The exact values come from a noiseless simulation. With up to 5 qubits a statevector is
      instant (32 amplitudes), no need for anything smarter.

BE CAREFUL WITH
    - Use the ORIGINAL circuit, not the compiled one: Statevector refuses circuits with measurements,
      and the original one is indexed by logical qubits, which is the convention we agreed on.
    - Qiskit order: in basis state number k, qubit i is bit i of k, counting from the RIGHT
      (k = 2 = 0b0010 means qubit 1 is 1). Same for Pauli labels: 'IIZI' is Z on qubit 1.
    - Statevector(...).probabilities() gives probabilities; .data gives complex amplitudes
      (probability = |amplitude|^2).
    - Easy checks to do yourselves: |0000> gives [1,1,1,1]; X on qubit 1 gives [1,-1,1,1];
      a 4-qubit GHZ state gives [0,0,0,0].
"""
