import heapq
import math


def dijkstra_classical(
    graph: dict[int, list[tuple[int, float]]],
    start: int,
    goal: int | None = None,
):
    dist = {v: math.inf for v in graph}
    prev = {v: None for v in graph}

    dist[start] = 0.0
    priority_queue = [(0.0, start)]
    visited = set()

    while priority_queue:
        current_distance, current_vertex = heapq.heappop(priority_queue)

        if current_vertex in visited:
            continue

        visited.add(current_vertex)

        if goal is not None and current_vertex == goal:
            break

        for neighbor, weight in graph[current_vertex]:
            new_distance = current_distance + weight

            if new_distance < dist[neighbor]:
                dist[neighbor] = new_distance
                prev[neighbor] = current_vertex
                heapq.heappush(priority_queue, (new_distance, neighbor))

    return dist, prev


def reconstruct_path(prev: dict[int, int | None], start: int, goal: int):
    if goal != start and prev[goal] is None:
        return None

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = prev[current]

    path.reverse()

    if not path or path[0] != start:
        return None

    return path


def frontier_candidates(
    graph: dict[int, list[tuple[int, float]]],
    visited: set[int],
    dist: dict[int, float],
) -> list[int]:
    candidates = set()

    for vertex in visited:
        for neighbor, _ in graph[vertex]:
            if neighbor not in visited and dist[neighbor] < math.inf:
                candidates.add(neighbor)

    return sorted(candidates)