import csv
import math

from qiskit_aer import AerSimulator

from quantum_dijkstra.config import ExperimentConfig
from quantum_dijkstra.graph.classical import frontier_candidates
from quantum_dijkstra.quantum.grover import grover_search_candidates


def hybrid_dijkstra_grover(
    graph: dict[int, list[tuple[int, float]]],
    start: int,
    goal: int | None,
    simulator: AerSimulator,
    config: ExperimentConfig,
    reporter=None,
):

    if start not in graph:
        raise ValueError(f"Počiatočný vrchol {start} nie je v grafe.")

    if goal is not None and goal not in graph:
        raise ValueError(f"Cieľový vrchol {goal} nie je v grafe.")

    dist = {v: math.inf for v in graph}
    prev = {v: None for v in graph}

    dist[start] = 0.0
    visited = {start}

    if goal == start:
        return dist, prev, []


    for neighbor, weight in graph[start]:
        if weight < dist[neighbor]:
            dist[neighbor] = weight
            prev[neighbor] = start

    history = []
    iteration = 0

    while True:
        candidates = frontier_candidates(graph, visited, dist)

        if not candidates:
            break

        finite_costs = [dist[v] for v in candidates if dist[v] < math.inf]

        if not finite_costs:
            break

        classical_best = min(candidates, key=lambda v: dist[v])

        current_candidate = max(candidates, key=lambda v: dist[v])
        current_threshold = dist[current_candidate]

        quantum_vertex = None
        counts = {}
        no_improvement_rounds = 0
        threshold_attempts = 0

        while threshold_attempts < config.rounds:
            threshold_attempts += 1

            marked_vertices = [
                v for v in candidates
                if dist[v] < current_threshold
            ]

            if not marked_vertices:
                break

            measured_vertex, counts = grover_search_candidates(
                candidates=candidates,
                marked_vertices=marked_vertices,
                simulator=simulator,
                config=config,
                reporter=reporter,
            )

            if (
                    measured_vertex is not None
                    and measured_vertex in candidates
                    and dist[measured_vertex] < current_threshold
            ):
                quantum_vertex = measured_vertex
                current_candidate = measured_vertex
                current_threshold = dist[measured_vertex]
                no_improvement_rounds = 0
            else:
                no_improvement_rounds += 1

            if no_improvement_rounds >= config.max_no_improvement_rounds:
                break

        if config.verify_quantum_choice:
            if quantum_vertex == classical_best:
                chosen_vertex = quantum_vertex
                selection_source = "quantum"
            else:
                chosen_vertex = classical_best
                selection_source = "classical_fallback"
        else:
            if quantum_vertex is not None:
                chosen_vertex = quantum_vertex
                selection_source = "quantum"
            else:
                chosen_vertex = classical_best
                selection_source = "classical_fallback"

        visited.add(chosen_vertex)

        for neighbor, weight in graph[chosen_vertex]:
            new_distance = dist[chosen_vertex] + weight

            if new_distance < dist[neighbor]:
                dist[neighbor] = new_distance
                prev[neighbor] = chosen_vertex

        history.append({
            "iteration": iteration,
            "chosen_vertex": chosen_vertex,
            "chosen_distance": dist[chosen_vertex],
            "frontier_size": len(candidates),
            "visited_size": len(visited),
            "selection_source": selection_source,
            "quantum_vertex": quantum_vertex,
            "classical_best": classical_best,
            "counts": str(counts),
        })

        iteration += 1

        if goal is not None and chosen_vertex == goal:
            break

    if reporter is not None:
        reporter.write_iteration_history(config.results_file, history)

    return dist, prev, history