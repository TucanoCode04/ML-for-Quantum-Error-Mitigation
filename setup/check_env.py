"""Check that the project environment works.

Run from the project folder, with the environment active:
    python setup/check_env.py
"""

import sys
import warnings

warnings.filterwarnings("ignore")
failed = 0

# 1. Python version
print("1. Python version...", end=" ")
if sys.version_info[:2] == (3, 12):
    print("PASS")
else:
    print("FAIL: you need Python 3.12")
    failed += 1

# 2. Simulate a small circuit on a fake copy of Lagrange (with noise)
print("2. Quantum simulation...", end=" ")
try:
    from iqm.qiskit_iqm import IQMFakeAdonis
    from qiskit import QuantumCircuit, transpile

    backend = IQMFakeAdonis()
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure_all()
    counts = backend.run(transpile(circuit, backend), shots=1000).result().get_counts()
    print("PASS")
except Exception as e:
    print("FAIL:", e)
    failed += 1

# 3. Zero-noise extrapolation library
print("3. Mitiq (ZNE)...", end=" ")
try:
    from mitiq.zne.scaling import fold_gates_at_random

    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cz(0, 1)
    fold_gates_at_random(circuit, 3.0)
    print("PASS")
except Exception as e:
    print("FAIL:", e)
    failed += 1

# 4. Machine learning libraries
print("4. Machine learning...", end=" ")
try:
    import torch
    from sklearn.ensemble import RandomForestRegressor

    RandomForestRegressor(n_estimators=10).fit([[0], [1], [2]], [0, 1, 2])
    torch.zeros(3)
    print("PASS")
except Exception as e:
    print("FAIL:", e)
    failed += 1

# Result
print()
if failed == 0:
    print("All good! Your environment is ready.")
else:
    print(f"{failed} check(s) failed. Bring your laptop to the next meeting.")
