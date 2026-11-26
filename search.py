"""Encode Berge–Fulkerson covers in SAT and check all returned covers directly."""

import argparse
from itertools import combinations
import json
from pathlib import Path

import networkx as nx
from pysat.formula import CNF
from pysat.solvers import Glucose4


def exact_count(variables, target):
    """Forbid every too-large set of true or false variables."""
    yield from (list(group) for group in combinations(variables, len(variables) - target + 1))
    yield from ([-x for x in group] for group in combinations(variables, target + 1))


def encode(graph):
    if not len(graph) or any(d != 3 for _, d in graph.degree()) or list(nx.bridges(graph)):
        raise ValueError("Expected a nonempty bridgeless cubic graph")
    edges = sorted(tuple(sorted(edge)) for edge in graph.edges())
    labels = {edge: i for i, edge in enumerate(edges)}
    incident = {v: sorted(labels[tuple(sorted((v, w)))] for w in graph[v]) for v in graph}
    clauses = CNF()
    for i in range(len(edges)):
        clauses.extend(exact_count([1 + 6 * i + color for color in range(6)], 2))
    for incident_edges in incident.values():
        for color in range(6):
            clauses.extend(exact_count([1 + 6 * i + color for i in incident_edges], 1))
    # The six colors can be permuted so the three edges at one vertex use these pairs.
    for pair, i in enumerate(incident[min(graph)]):
        clauses.append([1 + 6 * i + 2 * pair])
        clauses.append([2 + 6 * i + 2 * pair])
    return edges, clauses


def check_cover(graph, edges, assignments):
    matched = [set() for _ in range(6)]
    for (u, v), colors in zip(edges, assignments, strict=True):
        if len(colors) != 2 or len(set(colors)) != 2:
            raise ValueError(f"Edge {(u, v)} does not have two distinct colors")
        for color in colors:
            if u in matched[color] or v in matched[color]:
                raise ValueError(f"Color {color} has two edges sharing an endpoint")
            matched[color].update((u, v))
    if any(vertices != set(graph) for vertices in matched):
        raise ValueError("Some color does not give a perfect matching")


def search(graph, export):
    edges, clauses = encode(graph)
    with Glucose4(bootstrap_with=clauses.clauses) as solver:
        model = solver.get_model() if solver.solve() else None
    if model is None:
        with Glucose4(bootstrap_with=clauses.clauses, with_proof=True) as solver:
            if solver.solve():
                raise RuntimeError("SAT and proof-producing solves disagree")
            clauses.to_file(str(export.with_suffix(".cnf")))
            export.with_suffix(".drat").write_text("\n".join(solver.get_proof()) + "\n", encoding="ascii")
        return {"status": "unsat-awaiting-proof-check", "cnf": str(export.with_suffix(".cnf"))}
    true_variables = set(model)
    assignments = [[c for c in range(6) if 1 + 6 * i + c in true_variables]
                   for i in range(len(edges))]
    check_cover(graph, edges, assignments)
    return {"status": "checked-cover", "matchings": [[edge for edge, colors in zip(edges, assignments)
                                                       if c in colors] for c in range(6)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", nargs="?", type=Path)
    parser.add_argument("--proof-prefix", type=Path, default=Path("berge-fulkerson-witness"))
    parser.add_argument("--summary", action="store_true", help="Omit positive matching certificates from output")
    args = parser.parse_args()
    # K4 has three distinct perfect matchings, each usable twice. The Petersen graph
    # has six distinct perfect matchings and each of its edges is in exactly two.
    for known in (nx.complete_graph(4), nx.petersen_graph()):
        assert search(known, args.proof_prefix)["status"] == "checked-cover"
    if args.corpus is not None:
        for idx, line in enumerate(args.corpus.read_bytes().splitlines()):
            graph = nx.from_graph6_bytes(line)
            result = search(graph, args.proof_prefix)
            if args.summary:
                result.pop("matchings", None)
            print(json.dumps({"record": idx, "order": len(graph), "graph6": line.decode(), **result}), flush=True)
            if result["status"] != "checked-cover":
                return


if __name__ == "__main__":
    main()
