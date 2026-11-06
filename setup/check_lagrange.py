"""Check that your account can access Lagrange.

Run from the project folder, with the environment active:
    python setup/check_lagrange.py

It only logs in and connects. It does NOT run anything on the machine.
"""

import os
import sys
import warnings

from iqm.qiskit_iqm import IQMProvider
from lagrangeclient.__main__ import main as login

warnings.filterwarnings("ignore")

# 1. Log in: open the link that appears and choose "PoliTo SSO"
print("1. Log in")
sys.argv = ["lagrangeclient"]
login()

# 2. Connect to Lagrange with the token we just got
print()
print("2. Connect to Lagrange...", end=" ")
os.environ["IQM_TOKENS_FILE"] = "tokens.json"
try:
    provider = IQMProvider("https://spark.quantum.linksfoundation.com/", quantum_computer="default")
    backend = provider.get_backend()
    print(f"PASS (connected, {backend.num_qubits} qubits)")
except Exception as e:
    if "reserved" in str(e):
        print("PASS (your account works, the machine is just booked by someone else right now)")
    else:
        print("FAIL:", e)
        print("Your account may not be enabled for Lagrange yet. Tell the coordinator.")
