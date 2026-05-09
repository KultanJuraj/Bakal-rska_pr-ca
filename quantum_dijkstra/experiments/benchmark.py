import csv
import math
import random
import time
from qiskit_aer import AerSimulator
from quantum_dijkstra.config import ExperimentConfig
from quantum_dijkstra.graph.classical import dijkstra_classical, reconstruct_path
from quantum_dijkstra.hybrid.dijkstra_grover import hybrid_dijkstra_grover


def costs_match(classical_cost: float, hybrid_cost: float) -> bool:
    if math.isinf(classical_cost) and math.isinf(hybrid_cost):
        return True

    return abs(classical_cost - hybrid_cost) < 1e-9


def run_benchmark(
    graph: dict[int, list[tuple[int, float]]],
    config: ExperimentConfig,
    num_runs: int,
    reporter=None,
):
    random.seed(config.seed)

    simulator = AerSimulator(
        max_parallel_threads=config.max_parallel_threads,
        seed_simulator=config.seed,
    )

    rows = []
    vertices = list(graph.keys())

    for run in range(num_runs):
        start = random.choice(vertices)
        goal = random.choice(vertices)

        while goal == start:
            goal = random.choice(vertices)

        print(f"\nRun {run}: {start} -> {goal}")

        t0 = time.perf_counter()
        classical_dist, classical_prev = dijkstra_classical(graph, start, goal)
        classical_time = time.perf_counter() - t0

        classical_path = reconstruct_path(classical_prev, start, goal)
        classical_cost = classical_dist[goal]

        t0 = time.perf_counter()
        hybrid_dist, hybrid_prev, history = hybrid_dijkstra_grover(
            graph=graph,
            start=start,
            goal=goal,
            simulator=simulator,
            config=config,
            reporter=reporter,
        )

        hybrid_time = time.perf_counter() - t0

        hybrid_path = reconstruct_path(hybrid_prev, start, goal)
        hybrid_cost = hybrid_dist[goal]

        match = costs_match(classical_cost, hybrid_cost)

        print(f"Classical: {classical_cost} ({classical_time:.6f}s)")
        print(f"Hybrid: {hybrid_cost} ({hybrid_time:.6f}s)")
        print("Match:", match)

    if not rows:
        return []

    if reporter is not None:
        reporter.write_benchmark(config.benchmark_file, rows)

    print("\nBenchmark saved to:", config.benchmark_file)

    return rows