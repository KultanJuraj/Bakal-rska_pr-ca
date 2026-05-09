from quantum_dijkstra.quantum.encoding import compact_encode_candidates


def test_compact_encoding():
    candidates = [13, 63, 86, 163]
    marked = [63, 163]

    index_to_vertex, marked_indices, q = compact_encode_candidates(candidates, marked)

    assert index_to_vertex == [13, 63, 86, 163]
    assert marked_indices == [1, 3]
    assert q == 2