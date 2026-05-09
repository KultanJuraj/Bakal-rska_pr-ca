import csv
from pathlib import Path


def load_graph_from_csv(path: Path, num_vertices: int) -> dict[int, list[tuple[int, float]]]:
    graph = {i: [] for i in range(num_vertices)}

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_columns = {"source", "target", "weight"}
        if not required_columns.issubset(reader.fieldnames or set()):
            raise ValueError("CSV súbor musí obsahovať stĺpce: source,target,weight")

        for row in reader:
            source = int(row["source"])
            target = int(row["target"])
            weight = float(row["weight"])

            if not (0 <= source < num_vertices and 0 <= target < num_vertices):
                raise ValueError(f"Vrchol mimo rozsahu: {source}->{target}")

            if weight < 0:
                raise ValueError("Dijkstrov algoritmus vyžaduje nezáporné váhy hrán.")

            graph[source].append((target, weight))

    return graph


def maybe_create_demo_graph(path: Path) -> None:
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    demo_edges = [
        (0, 1, 1),
        (0, 2, 4),
        (1, 3, 2),
        (2, 3, 1),
        (3, 4, 3),
        (4, 10, 2),
        (10, 15, 5),
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "weight"])
        writer.writerows(demo_edges)