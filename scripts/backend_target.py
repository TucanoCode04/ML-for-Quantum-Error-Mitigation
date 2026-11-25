from qiskit import transpile
from qiskit.circuit.random import random_circuit
from iqm.qiskit_iqm import IQMFakeAdonis

TRANSPILER_SEED = 0 

def compile_circuit(circuit, backend, seed):
    #placeholder
    measured = circuit.copy()
    measured.measure_all()
    return transpile(measured, target=backend.target,
                     optimization_level=1, seed_transpiler=seed)

backend=IQMFakeAdonis()

qc = random_circuit(4, depth=2, max_operands=2, seed=42)
print(qc.draw())
print(qc.count_ops())

compiled=compile_circuit(qc,backend,TRANSPILER_SEED)
print("Number of CZ gates:", compiled.count_ops().get("cz",0))
print(compiled.draw(fold=150))
print(compiled.layout.final_index_layout())

"""small thing I noticed while testing:
when I transpile with backend=IQMFakeAdonis(), the qubit numbers in the compiled circuit
don't match the chip. The CZs show up between qubits that aren't even connected.
If I use target=backend.target instead, the numbers look right (every CZ goes through qubit 2).
The CZ count is the same both ways and the results still come out correct, so I think it's
only a problem when reading the circuit. Maybe worth checking for compile.py?"""