import math
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from quantum_dijkstra.config import ExperimentConfig
from quantum_dijkstra.quantum.encoding import (
    compact_encode_candidates,
    measured_bitstring_to_index,
)
from quantum_dijkstra.quantum.oracle import build_oracle_for_marked_set
from quantum_dijkstra.quantum.diffuser import build_diffuser


def optimal_grover_iterations(search_size: int, marked_count: int) -> int:
    if marked_count <= 0 or search_size <= 0:
        return 0


    if marked_count >= search_size / 2:
        return 0

    return max(1, round((math.pi / 4) * math.sqrt(search_size / marked_count)))


def grover_search_candidates(
    candidates: list[int],
    marked_vertices: list[int],
    simulator: AerSimulator,
    config: ExperimentConfig,
    reporter=None,
):

    if not candidates or not marked_vertices:
        return None, {}

    index_to_vertex, marked_indices, q = compact_encode_candidates(
        candidates,
        marked_vertices,
    )

    if not marked_indices:
        return None, {}

    flag_qubit = q
    total_qubits = q + 1
    vertex_qubits = list(range(q))

    circuit = QuantumCircuit(total_qubits, q)


    circuit.h(vertex_qubits)

    circuit.x(flag_qubit)
    circuit.h(flag_qubit)

    oracle = build_oracle_for_marked_set(marked_indices, q)
    diffuser = build_diffuser(q)

    search_size = 2 ** q
    grover_iterations = min(
        config.max_grover_iters,
        optimal_grover_iterations(search_size, len(marked_indices)),
    )

    for _ in range(grover_iterations):
        circuit.compose(oracle, inplace=True)
        circuit.compose(diffuser, qubits=vertex_qubits, inplace=True)

    circuit.measure(vertex_qubits, range(q))

    transpiled_circuit = transpile(
        circuit,
        simulator,
        optimization_level=1,
        seed_transpiler=config.seed,
    )

    result = simulator.run(
        transpiled_circuit,
        shots=config.shots,
    ).result()

    counts = result.get_counts()

    if not counts:
        return None, {}

    valid_marked_counts = {
        bitstring: count
        for bitstring, count in counts.items()
        if measured_bitstring_to_index(bitstring) in marked_indices
    }

    if not valid_marked_counts:
        if config.log_iterations:
            config.iteration_log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config.iteration_log_file, "a", encoding="utf-8") as f:
                f.write(f"Candidates: {candidates}\n")
                f.write(f"Marked vertices: {marked_vertices}\n")
                f.write(f"Compact marked indices: {marked_indices}\n")
                f.write(f"Candidate qubits: {q}\n")
                f.write(f"Search size: {search_size}\n")
                f.write(f"Grover iterations: {grover_iterations}\n")
                f.write(f"Counts: {counts}\n")
                f.write("Measured vertex: None\n")
                f.write("Reason: no valid marked state measured\n\n")

        return None, counts

    best_bitstring = max(valid_marked_counts, key=valid_marked_counts.get)
    measured_index = measured_bitstring_to_index(best_bitstring)
    measured_vertex = index_to_vertex[measured_index]

    if config.log_iterations and reporter is not None:
        reporter.append_quantum_log(
            path=config.iteration_log_file,
            candidates=candidates,
            marked_vertices=marked_vertices,
            marked_indices=marked_indices,
            candidate_qubits=q,
            search_size=search_size,
            grover_iterations=grover_iterations,
            counts=counts,
            measured_bitstring=best_bitstring,
            measured_index=measured_index,
            measured_vertex=measured_vertex,
        )

    if config.draw_circuit:
        config.circuit_image_file.parent.mkdir(parents=True, exist_ok=True)
        circuit.draw(output="mpl", filename=str(config.circuit_image_file))

    return measured_vertex, counts