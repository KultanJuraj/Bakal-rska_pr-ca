import math


def compact_encode_candidates(candidates: list[int], marked_vertices: list[int]):

    index_to_vertex = list(candidates)
    vertex_to_index = {vertex: index for index, vertex in enumerate(index_to_vertex)}

    marked_indices = [
        vertex_to_index[v]
        for v in marked_vertices
        if v in vertex_to_index
    ]

    number_of_candidates = len(index_to_vertex)
    qubits = max(1, math.ceil(math.log2(max(1, number_of_candidates))))

    return index_to_vertex, marked_indices, qubits


def measured_bitstring_to_index(bitstring: str) -> int:
    return int(bitstring[::-1], 2)