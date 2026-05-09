from qiskit_aer import AerSimulator

from quantum_dijkstra.config import ExperimentConfig
from quantum_dijkstra.graph.loader import load_graph_from_csv
from quantum_dijkstra.experiments.benchmark import run_benchmark
from quantum_dijkstra.experiments.reporter import ExperimentReporter


class ExperimentRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.reporter = ExperimentReporter(config.output_dir)

    def load_graph(self):
        if not self.config.graph_file.exists():
            raise FileNotFoundError(
                f"Graph file not found: {self.config.graph_file.resolve()}"
            )

        graph = load_graph_from_csv(
            path=self.config.graph_file,
            num_vertices=self.config.num_vertices,
        )

        edge_count = sum(len(edges) for edges in graph.values())

        print("Using graph file:", self.config.graph_file.resolve())
        print("Vertices:", self.config.num_vertices)
        print("Edges loaded:", edge_count)

        return graph, edge_count

    def run(self, num_runs: int):
        graph, edge_count = self.load_graph()

        rows = run_benchmark(
            graph=graph,
            config=self.config,
            num_runs=num_runs,
            reporter=self.reporter,
        )

        matches = sum(1 for row in rows if row["match"])
        total = len(rows)

        summary_lines = [
            "HYBRID DIJKSTRA-GROVER EXPERIMENT SUMMARY",
            "",
            f"Graph file: {self.config.graph_file.resolve()}",
            f"Vertices: {self.config.num_vertices}",
            f"Edges: {edge_count}",
            f"Runs: {total}",
            f"Matches: {matches}/{total}" if total else "Matches: 0/0",
            f"Shots: {self.config.shots}",
            f"Seed: {self.config.seed}",
            f"Rounds: {self.config.rounds}",
            f"Max Grover iterations: {self.config.max_grover_iters}",
            f"Verify quantum choice: {self.config.verify_quantum_choice}",
            f"Log iterations: {self.config.log_iterations}",
        ]

        self.reporter.write_summary(self.config.summary_file, summary_lines)

        print("\nSummary saved to:", self.config.summary_file)

        return rows