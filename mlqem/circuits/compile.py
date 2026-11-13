"""Compile circuits for Lagrange.                                 Group: Circuits & hardware

WHAT THIS FILE SHOULD DO FOR NOW
Take an original circuit (no measurements) and return the version Lagrange can run: measurement on
every qubit, only native gates (r and cz), qubits placed on the star topology.
generate.py uses it to count CZs, the simulation group uses its output to get the noisy values,
and later the hardware runs and ZNE use it too. So it's worth doing it once, well.

WHAT NEEDS TO BE IMPLEMENTED (names and details are up to you)
    - A function that, given a circuit, a backend and a seed, adds measurements on all qubits and
      transpiles for the backend. It must not modify the circuit it receives (work on a copy).

BE CAREFUL WITH
    - Add the measurements BEFORE transpiling. While routing, the compiler moves logical qubits
      around the chip (logical 0 can end on physical 3). If the measurement "logical i -> bit i" is
      already there, the compiler moves it along, so bit i of the results is always logical qubit i.
      Adding measurements after compiling means working out yourself where every qubit went.
    - Keep the seed of the transpiler and the optimization level FIXED and the same for everyone:
      both change the number of CZs. Write down which ones we use.
    - After compiling, compiled.layout.final_index_layout()[i] tells on which physical qubit logical
      qubit i ended up. The models group needs it, so don't throw the layout away.
    - Check that the result only contains r, cz, measure (and maybe barrier).

LATER (keep the door open, don't do it now)
    - ZNE folds the CZs, and Mitiq can't read IQM's r gate. A way to compile to rx/ry/rz + cz
      instead of r + cz (e.g. an option for the basis gates) will be needed.
    - hardware.py will send many compiled circuits in ONE job (Lagrange has a FIFO queue, one job per
      circuit would take forever), and save the raw counts, the date and the calibration data of the
      day together with the results. If the error says "Slot reserved to another project", wait and retry.
"""


# Imports
from qiskit import QuantumCircuit, transpile
from qiskit.providers import BackendV2

# CONSTANTS, used for all programs
TRANSPILER_SEED = 10
OPT_LEVEL = 2

def check_native_gates(compiled, backend: BackendV2, basis=None):
    base_gates = basis if basis is not None else backend.target.operation_names
    allowed_gates = set(base_gates) | {"measure", "barrier"}
    gates_used = set(compiled.count_ops().keys())

    # Sanity check forn non-allowed gates
    non_allowed = gates_used-allowed_gates
    if non_allowed:
        raise ValueError(f"Non-allowed gates in circuit. Gates: {non_allowed}")

def compile_for_backend(circuit: QuantumCircuit, backend: BackendV2, seed=TRANSPILER_SEED, opt_level=OPT_LEVEL, basis=None):
    measured = circuit.measure_all(inplace=False) # Measured copy
    compiled = transpile(circuits=measured, backend=backend, basis_gates=basis, seed_transpiler=seed, optimization_level=opt_level)

    check_native_gates(compiled, backend, basis)

    return compiled