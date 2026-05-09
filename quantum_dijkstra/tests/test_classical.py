from quantum_dijkstra.graph.classical import dijkstra_classical, reconstruct_path


def test_dijkstra_small_graph():
    graph = {
        0: [(1, 1.0), (2, 4.0)],
        1: [(2, 2.0), (3, 5.0)],
        2: [(3, 1.0)],
        3: [],
    }

    dist, prev = dijkstra_classical(graph, start=0, goal=3)
    path = reconstruct_path(prev, start=0, goal=3)

    assert dist[3] == 4.0
    assert path == [0, 1, 2, 3]