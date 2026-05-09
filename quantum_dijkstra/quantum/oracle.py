from functools import lru_cache
from qiskit import QuantumCircuit


def apply_mark_index(
    circuit: QuantumCircuit,
    index: int,
    vertex_qubits: list[int],
    flag_qubit: int,
) -> None:

    bits = format(index, f"0{len(vertex_qubits)}b")[::-1]

    for i, bit in enumerate(bits):
        if bit == "0":
            circuit.x(vertex_qubits[i])

    circuit.mcx(vertex_qubits, flag_qubit)

    for i, bit in enumerate(bits):
        if bit == "0":
            circuit.x(vertex_qubits[i])


@lru_cache(maxsize=512)
def build_oracle_for_marked_set_cached(
    marked_indices_tuple: tuple[int, ...],
    q: int,
) -> QuantumCircuit:

    flag_qubit = q
    total_qubits = q + 1
    vertex_qubits = list(range(q))

    circuit = QuantumCircuit(total_qubits, name="Oracle")

    for marked_index in marked_indices_tuple:
        apply_mark_index(circuit, marked_index, vertex_qubits, flag_qubit)

    return circuit


def build_oracle_for_marked_set(marked_indices: list[int], q: int) -> QuantumCircuit:
    unique_indices = tuple(sorted(set(marked_indices)))
    return build_oracle_for_marked_set_cached(unique_indices, q)