from qiskit_aer import AerSimulator

from quantum_dijkstra.config import ExperimentConfig
from quantum_dijkstra.graph.classical import dijkstra_classical
from quantum_dijkstra.hybrid.dijkstra_grover import hybrid_dijkstra_grover


def test_hybrid_matches_classical_on_small_graph():
    graph = {
        0: [(1, 1.0), (2, 4.0)],
        1: [(2, 2.0), (3, 5.0)],
        2: [(3, 1.0)],
        3: [],
    }

    config = ExperimentConfig(
        num_vertices=4,
        shots=256,
        seed=42,
        rounds=1,
        max_grover_iters=3,
        verify_quantum_choice=True,
        log_iterations=False,
    )

    simulator = AerSimulator(seed_simulator=config.seed)

    classical_dist, _ = dijkstra_classical(graph, start=0, goal=3)

    hybrid_dist, _, _ = hybrid_dijkstra_grover(
        graph=graph,
        start=0,
        goal=3,
        simulator=simulator,
        config=config,
        reporter=None,
    )

    assert hybrid_dist[3] == classical_dist[3]