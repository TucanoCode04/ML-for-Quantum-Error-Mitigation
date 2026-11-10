"""Noisy <Z_i> values from measurements.                          Group: Simulation & ZNE

WHAT THIS FILE SHOULD DO FOR NOW
Run a compiled circuit on a noisy backend and turn the measurement results into the vector
[<Z_0>, ..., <Z_{n-1}>]. For now the backend is IQMFakeAdonis (a simulator with a noise model of a
chip like Lagrange); later the very same code must work on the real Lagrange.
These noisy values are the main input of the ML models.

WHAT NEEDS TO BE IMPLEMENTED (names and details are up to you)
    - Counts -> <Z_i>: from a dict like {'0010': 950, '0000': 50} to an array of n_qubits values.
      Keep this separate from running: it can be checked by hand without any backend, and it
      works the same for counts from the simulator and from Lagrange.
    - Run on a backend: compiled circuit(s), backend, shots, seed  ->  <Z_i> values.

FROM COUNTS TO <Z_i>
    Counts say how many times each bitstring came out. For qubit i:
        <Z_i> = (shots where qubit i was 0 - shots where qubit i was 1) / total shots
    It's the same formula as the exact one, with measured frequencies instead of exact probabilities.

WHAT THE PAPER DOES
    - Noisy expectation values are estimated from a finite number of shots, so they contain both
      the hardware noise and statistical noise. Our shot number (4000 for now) must stay the same
      for the whole dataset.

BE CAREFUL WITH
    - In a key like '0010' the RIGHTMOST character is qubit 0. Getting this wrong mixes up the
      qubits silently, everything still "works" but the data is garbage.
    - Keys can contain spaces if a circuit has more than one classical register.
    - Thanks to the measurements added before compiling, bit i is logical qubit i, no need to
      translate physical qubits here.
    - Fix the simulator seed (seed_simulator) so results can be reproduced.
    - With 4000 shots the statistical error is about 1/sqrt(4000) ~ 0.016 per value: no model can
      go much below that, keep it in mind when reading the results.
    - Think of running a LIST of circuits in one call from the start: on Lagrange we will send
      many circuits per job because of the queue.

LATER: zne.py (baseline to beat)
    Digital gate folding: replace every CZ with CZ CZ CZ (CZ is its own inverse, so the circuit
    does the same thing but with ~3x the CZ noise). Measure at noise factors 1 and 3 and extrapolate
    linearly to 0:  Z(0) = (3 Z(1) - Z(3)) / 2.  Mitiq can do it but can't read IQM's r gate,
    so either fold by hand or compile to rx/ry/rz + cz first.
"""
