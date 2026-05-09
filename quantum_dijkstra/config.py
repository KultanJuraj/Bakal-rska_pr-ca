import datetime
import random
from dataclasses import dataclass
from pathlib import Path

import yaml

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExperimentConfig:
    num_vertices: int = 1024
    shots: int = 8192
    seed: int = 42

    max_parallel_threads: int = 6
    max_grover_iters: int = 10
    max_no_improvement_rounds: int = 2
    rounds : int = 10

    graph_file: Path = Path("data/graph1024.csv")

    output_dir: Path = Path("outputs")
    benchmark_file: Path = Path("outputs/benchmark.csv")
    results_file: Path = Path("outputs/results.csv")
    iteration_log_file: Path = Path("outputs/iteration_file.txt")
    summary_file: Path = Path("outputs/summary.txt")
    circuit_image_file: Path = Path("outputs/circuit-mpl.jpeg")

    verify_quantum_choice: bool = True
    log_iterations: bool = True
    draw_circuit: bool = False

    use_ancilla_mcx: bool = False




def load_config_from_yaml(path: Path) -> ExperimentConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    path_fields = {
        "graph_file",
        "benchmark_file",
        "results_file",
        "iteration_log_file",
        "circuit_image_file",
    }

    for field in path_fields:
        if field in data:
            data[field] = Path(data[field])

    return ExperimentConfig(**data)