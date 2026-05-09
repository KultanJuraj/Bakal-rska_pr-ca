import csv
from pathlib import Path
from typing import Any


class ExperimentReporter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_benchmark(self, path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        if not rows:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def write_iteration_history(self, path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        if not rows:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def append_quantum_log(
        self,
        path: Path,
        candidates: list[int],
        marked_vertices: list[int],
        marked_indices: list[int],
        candidate_qubits: int,
        search_size: int,
        grover_iterations: int,
        counts: dict[str, int],
        measured_bitstring: str | None,
        measured_index: int | None,
        measured_vertex: int | None,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "a", encoding="utf-8") as f:
            f.write(f"Candidates: {candidates}\n")
            f.write(f"Marked vertices: {marked_vertices}\n")
            f.write(f"Compact marked indices: {marked_indices}\n")
            f.write(f"Candidate qubits: {candidate_qubits}\n")
            f.write(f"Search size: {search_size}\n")
            f.write(f"Grover iterations: {grover_iterations}\n")
            f.write(f"Counts: {counts}\n")
            f.write(f"Measured bitstring: {measured_bitstring}\n")
            f.write(f"Measured index: {measured_index}\n")
            f.write(f"Measured vertex: {measured_vertex}\n")
            f.write("-" * 80 + "\n\n")

    def write_summary(self, path: Path, lines: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")