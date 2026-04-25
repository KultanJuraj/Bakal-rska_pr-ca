import csv
import math
import random
import heapq
from pathlib import Path
import time

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator




NUM_VERTICES = 2048
VERTEX_QUBITS = 11
TOTAL_QUBITS = 22
FLAG_QUBIT = 11
ANCILLA_START = 12

GRAPH_FILE = Path(__file__).parent / "graph.csv"
RESULTS_FILE = "results.csv"
SUMMARY_FILE = "summary.txt"

SHOTS = 128

sim = AerSimulator(max_parallel_threads=6)



def load_graph_from_csv(path: str, num_vertices: int = NUM_VERTICES):
    graph = {i: [] for i in range(num_vertices)}

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"source", "target", "weight"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError("CSV must have columns: source,target,weight")

        for row in reader:
            u = int(row["source"])
            v = int(row["target"])
            w = float(row["weight"])

            if not (0 <= u < num_vertices and 0 <= v < num_vertices):
                raise ValueError(f"Vertex out of range: {u}->{v}")

            graph[u].append((v, w))

    return graph



def dijkstra_classical(graph, start, goal=None):
    dist = {v: math.inf for v in graph}
    prev = {v: None for v in graph}
    dist[start] = 0.0

    pq = [(0.0, start)]
    visited = set()

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        if goal is not None and u == goal:
            break

        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    return dist, prev


def reconstruct_path(prev, start, goal):
    if goal != start and prev[goal] is None:
        return None

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    if path[0] != start:
        return None
    return path



def frontier_candidates(graph, visited, dist):
    candidates = set()

    for u in visited:
        for v, _ in graph[u]:
            if v not in visited and dist[v] < math.inf:
                candidates.add(v)

    return sorted(candidates)


def random_marked_vertex(candidates, dist, threshold):
    marked = [v for v in candidates if dist[v] < threshold]
    if not marked:
        return None
    return random.choice(marked)



def apply_mark_vertex(qc: QuantumCircuit, vertex: int, vertex_qubits, flag_qubit: int):

    bits = format(vertex, f"0{len(vertex_qubits)}b")

    for i, bit in enumerate(bits):
        if bit == "0":
            qc.x(vertex_qubits[i])

    qc.mcx(vertex_qubits, flag_qubit)

    for i, bit in enumerate(bits):
        if bit == "0":
            qc.x(vertex_qubits[i])


def build_oracle_for_marked_set(marked_vertices):

    qc = QuantumCircuit(TOTAL_QUBITS)

    vertex_qubits = list(range(VERTEX_QUBITS))
    flag = FLAG_QUBIT

    qc.x(flag)
    qc.h(flag)

    for v in marked_vertices:
        apply_mark_vertex(qc, v, vertex_qubits, flag)


    return qc


def build_diffuser():
    qc = QuantumCircuit(VERTEX_QUBITS)

    qc.h(range(VERTEX_QUBITS))
    qc.x(range(VERTEX_QUBITS))

    qc.h(VERTEX_QUBITS - 1)
    qc.mcx(list(range(VERTEX_QUBITS - 1)), VERTEX_QUBITS - 1)
    qc.h(VERTEX_QUBITS - 1)

    qc.x(range(VERTEX_QUBITS))
    qc.h(range(VERTEX_QUBITS))

    return qc


def optimal_grover_iterations(search_size, marked_count):
    if marked_count <= 0 or search_size <= 0:
        return 0
    return max(1, round((math.pi / 4) * math.sqrt(search_size / marked_count)))


def grover_search_candidates(candidates, marked_vertices, shots=SHOTS):
    if not marked_vertices:
        return None, {}

    qc = QuantumCircuit(TOTAL_QUBITS, VERTEX_QUBITS)

    vertex_qubits = list(range(VERTEX_QUBITS))

    qc.h(vertex_qubits)

    oracle = build_oracle_for_marked_set(marked_vertices)
    diffuser = build_diffuser()

    grover_iters = min(5, optimal_grover_iterations(2 ** VERTEX_QUBITS, len(marked_vertices)))

    for _ in range(grover_iters):
        qc.compose(oracle, inplace=True)
        qc.compose(diffuser, qubits=vertex_qubits, inplace=True)

    qc.measure(vertex_qubits, range(VERTEX_QUBITS))

    tqc = transpile(qc, sim, optimization_level=1)
    result = sim.run(tqc, shots=shots).result()
    counts = result.get_counts()

    best_bitstring = max(counts, key=counts.get)
    measured_vertex = int(best_bitstring, 2)

    return measured_vertex, counts


def hybrid_dijkstra_grover(graph, start, goal=None, results_file=RESULTS_FILE):
    dist = {v: math.inf for v in graph}
    prev = {v: None for v in graph}
    visited = set()

    dist[start] = 0.0

    history = []
    iteration = 0

    while True:
        candidates = frontier_candidates(graph, visited | ({start} if not visited else set()), dist)

        if not visited:
            candidates = sorted(v for v, _ in graph[start])
            for v, w in graph[start]:
                if w < dist[v]:
                    dist[v] = w
                    prev[v] = start

        if not candidates:
            break

        finite_costs = [dist[v] for v in candidates if dist[v] < math.inf]
        if not finite_costs:
            break

        current_best = random.choice(finite_costs)
        best_vertex = None

        rounds = max(4, int(math.sqrt(len(candidates))) + 2)

        for _ in range(rounds):
            marked = [v for v in candidates if dist[v] < current_best]
            measured_vertex, counts = grover_search_candidates(candidates, marked, shots=SHOTS)

            if measured_vertex in candidates and dist[measured_vertex] < current_best:
                current_best = dist[measured_vertex]
                best_vertex = measured_vertex

        if best_vertex is None:
            best_vertex = min(candidates, key=lambda v: dist[v])

        visited.add(best_vertex)

        for nbr, w in graph[best_vertex]:
            nd = dist[best_vertex] + w
            if nd < dist[nbr]:
                dist[nbr] = nd
                prev[nbr] = best_vertex

        history.append({
            "iteration": iteration,
            "chosen_vertex": best_vertex,
            "chosen_distance": dist[best_vertex],
            "frontier_size": len(candidates),
            "visited_size": len(visited),
        })
        iteration += 1

        if goal is not None and best_vertex == goal:
            break

    with open(results_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["iteration", "chosen_vertex", "chosen_distance", "frontier_size", "visited_size"]
        )
        writer.writeheader()
        writer.writerows(history)

    return dist, prev, history



def maybe_create_demo_graph(path: str):
    if Path(path).exists():
        return

    # Small connected demo embedded in a 1024-vertex namespace.
    demo_edges = [
        (0, 1, 1),
        (0, 2, 4),
        (1, 3, 2),
        (2, 3, 1),
        (3, 4, 3),
        (4, 10, 2),
        (10, 20, 5),
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "weight"])
        for row in demo_edges:
            writer.writerow(row)



def benchmark(graph, num_runs=10, output_file="benchmark1.csv"):

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
        hybrid_dist, hybrid_prev, history = hybrid_dijkstra_grover(graph, start, goal)
        hybrid_time = time.perf_counter() - t0

        hybrid_path = reconstruct_path(hybrid_prev, start, goal)
        hybrid_cost = hybrid_dist[goal]

        match = (classical_cost == hybrid_cost)
        print(f"Classical: {classical_cost} ({classical_time:.4f}s)")
        print(f"Hybrid: {hybrid_cost} ({hybrid_time:.4f}s)")
        print("Match:", match)

        rows.append({
            "run": run,
            "start": start,
            "goal": goal,

            "classical_time": classical_time,
            "hybrid_time": hybrid_time,

            "classical_cost": classical_cost,
            "hybrid_cost": hybrid_cost,

            "classical_path": classical_path,
            "hybrid_path": hybrid_path,

            "match": match,
            "hybrid_iterations": len(history),
        })


    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("\nBenchmark saved to:", output_file)

def main():
    #print("Graph file path:", GRAPH_FILE)
    #print("File exists:", Path(GRAPH_FILE).exists())
    maybe_create_demo_graph(GRAPH_FILE)

    graph = load_graph_from_csv(GRAPH_FILE, num_vertices=NUM_VERTICES)


    benchmark(graph, num_runs=5)

    '''start = 0
    goal = 63

    classical_dist, classical_prev = dijkstra_classical(graph, start, goal)
    classical_path = reconstruct_path(classical_prev, start, goal)
    classical_cost = classical_dist[goal]

    hybrid_dist, hybrid_prev, history = hybrid_dijkstra_grover(graph, start, goal, RESULTS_FILE)
    hybrid_path = reconstruct_path(hybrid_prev, start, goal)
    hybrid_cost = hybrid_dist[goal]

        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(f"Vertices supported: {NUM_VERTICES}\n")
        f.write(f"Qubits used: {TOTAL_QUBITS}\n")
        f.write(f"Vertex register qubits: {VERTEX_QUBITS}\n\n")

        f.write(f"Start: {start}\n")
        f.write(f"Goal: {goal}\n\n")

        f.write("CLASSICAL RESULT\n")
        f.write(f"Cost: {classical_cost}\n")
        f.write(f"Path: {classical_path}\n\n")

        f.write("HYBRID RESULT\n")
        f.write(f"Cost: {hybrid_cost}\n")
        f.write(f"Path: {hybrid_path}\n\n")

        f.write(f"Match: {classical_cost == hybrid_cost and classical_path == hybrid_path}\n")

    print("===== RESULTS =====")
    print(f"Vertices supported: {NUM_VERTICES}")
    print(f"Qubits used: {TOTAL_QUBITS}")
    print()
    print("Classical cost:", classical_cost)
    print("Classical path:", classical_path)
    print()
    print("Hybrid cost:", hybrid_cost)
    print("Hybrid path:", hybrid_path)
    print()
    print("Match:", classical_cost == hybrid_cost and classical_path == hybrid_path)
    print()
    print(f"Wrote iteration log to: {RESULTS_FILE}")
    print(f"Wrote summary to: {SUMMARY_FILE}")'''


if __name__ == "__main__":
    main()