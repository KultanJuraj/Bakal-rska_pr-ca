from functools import lru_cache
from qiskit import QuantumCircuit


@lru_cache(maxsize=64)
def build_diffuser(q: int) -> QuantumCircuit:
    circuit = QuantumCircuit(q, name="Diffuser")

    circuit.h(range(q))
    circuit.x(range(q))

    if q == 1:
        circuit.z(0)
    else:
        circuit.h(q - 1)
        circuit.mcx(list(range(q - 1)), q - 1)
        circuit.h(q - 1)

    circuit.x(range(q))
    circuit.h(range(q))

    return circuit