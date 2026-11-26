"""Generate deterministic five-edge splices of published cubic graphs."""

import argparse
from itertools import combinations
from pathlib import Path
from random import Random

import networkx as nx


def five_poles(graph):
    for center in graph:
        for end_a, end_b in combinations(graph[center], 2):
            if graph.has_edge(end_a, end_b):
                continue
            path = {center, end_a, end_b}
            terminals = sorted(v for u in path for v in graph[u] if v not in path)
            if len(set(terminals)) != 5:
                continue
            pole = graph.copy()
            pole.remove_nodes_from(path)
            if nx.is_connected(pole):
                yield pole, terminals


def splices(graphs, count, seed):
    rng = Random(seed)
    pools = [list(five_poles(graph)) for graph in graphs]
    if any(not poles for poles in pools):
        raise ValueError("Each source graph must have a connected five-pole")
    seen = set()
    for _ in range(count * 100):
        left, right = rng.choices(pools, k=2)
        a, terminals_a = rng.choice(left)
        b, terminals_b = rng.choice(right)
        left_labels = {v: i for i, v in enumerate(sorted(a))}
        right_labels = {v: i + len(a) for i, v in enumerate(sorted(b))}
        joined = nx.compose(nx.relabel_nodes(a, left_labels), nx.relabel_nodes(b, right_labels))
        for u, v in zip(terminals_a, rng.sample(terminals_b, 5), strict=True):
            joined.add_edge(left_labels[u], right_labels[v])
        if any(True for _ in nx.bridges(joined)):
            continue
        assert all(degree == 3 for _, degree in joined.degree())
        encoding = nx.to_graph6_bytes(joined, header=False)
        if encoding in seen:
            continue
        seen.add(encoding)
        yield encoding
        if len(seen) == count:
            return
    raise RuntimeError(f"Generated only {len(seen)} of {count} requested distinct inputs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20261125)
    args = parser.parse_args()
    graphs = nx.read_graph6(args.source)
    with args.output.open("wb") as destination:
        for encoding in splices(graphs, args.count, args.seed):
            destination.write(encoding)


if __name__ == "__main__":
    main()
