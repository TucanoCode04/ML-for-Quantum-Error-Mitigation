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
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def compute_exact_z_expectations(circuit: QuantumCircuit) -> np.ndarray:
  """
    Compute the exact expectation values <Z_i> for each qubit of an ideal
    (noiseless) quantum circuit without measurements.

    Args:
        circuit: Original QuantumCircuit (without measurement operations).

    Returns:
        np.ndarray: 1D float array of length n_qubits with values in [-1, 1].
    """
  # 1. Remove any final measurements for safety and compute the exact Statevector
  clean_circuit = circuit.remove_final_measurements(inplace=False)
  sv = Statevector(clean_circuit)

  # 2. Extract the array of 2^n state probabilities
  probs = sv.probabilities()
  n_qubits = clean_circuit.num_qubits
  n_states = len(probs)  # equal to 2**n_qubits

  z_expectations = np.zeros(n_qubits, dtype=float)

  # 3. Compute <Z_i> = P(qubit i is 0) - P(qubit i is 1) for each qubit i
  for i in range(n_qubits):
    exp_val = 0.0
    for k in range(n_states):
      # Check the i-th bit of basis state index k 
      bit_i = (k >> i) & 1

      if bit_i == 0:
        exp_val += probs[k]
      else:
        exp_val -= probs[k]

    z_expectations[i] = exp_val

  return z_expectations


if __name__ == "__main__":
  # Test 1: State |0000> -> expected [1., 1., 1., 1.]
  qc1 = QuantumCircuit(4)
  print("Test |0000>:", compute_exact_z_expectations(qc1))

  # Test 2: Bring X on qubit 1 -> expected [1., -1., 1., 1.]
  qc2 = QuantumCircuit(4)
  qc2.x(1)
  print("Test X(1):  ", compute_exact_z_expectations(qc2))

  # Test 3: State GHZ with 4 qubit -> expected [0., 0., 0., 0.]
  qc3 = QuantumCircuit(4)
  qc3.h(0)
  qc3.cx(0, 1)
  qc3.cx(1, 2)
  qc3.cx(2, 3)
  print("Test GHZ:   ", compute_exact_z_expectations(qc3))