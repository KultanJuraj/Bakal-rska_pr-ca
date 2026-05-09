import argparse
from pathlib import Path

from quantum_dijkstra.experiments.runner import ExperimentRunner
from quantum_dijkstra.config import ExperimentConfig, load_config_from_yaml


def parse_args():
    parser = argparse.ArgumentParser(
        description="Hybridný Dijkstra-Grover algoritmus pre hľadanie najkratšej cesty."
    )

    parser.add_argument("--vertices", type=int, default=1024)
    parser.add_argument("--graph", type=Path, default=Path("data/graph1024.csv"))
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--shots", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument("--benchmark-file", type=Path, default=Path("outputs/benchmark.csv"))
    parser.add_argument("--results-file", type=Path, default=Path("outputs/results.csv"))
    parser.add_argument("--iteration-log", type=Path, default=Path("outputs/iteration_file.txt"))

    parser.add_argument("--max-grover-iters", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--threads", type=int, default=6)

    # Default: bez safe fallback overenia.
    # Ak chceš bezpečný režim, spustíš s --verify.
    parser.add_argument("--verify", action="store_true")

    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--draw-circuit", action="store_true")
    parser.add_argument("--config", type=Path, default=None)

    return parser.parse_args()


def main():
    args = parse_args()

    if args.config is not None:
        config = load_config_from_yaml(args.config)
    else:
        config = ExperimentConfig(
            num_vertices=args.vertices,
            shots=args.shots,
            seed=args.seed,
            max_parallel_threads=args.threads,
            max_grover_iters=args.max_grover_iters,
            rounds=args.rounds,
            graph_file=args.graph,
            benchmark_file=args.benchmark_file,
            results_file=args.results_file,
            iteration_log_file=args.iteration_log,
            verify_quantum_choice=not args.no_verify,
            log_iterations=not args.no_log,
            draw_circuit=args.draw_circuit,
        )

    runner = ExperimentRunner(config)
    runner.run(num_runs=args.runs)


if __name__ == "__main__":
    main()