"""Verify a bridgeless splice whose covers all use the same boundary type."""

import argparse
import json
from pathlib import Path

import networkx as nx
from pysat.solvers import Glucose4

from five_cut import PORTS, glue
from search import encode, search


def certify(record, permutation, prefix):
    pole_data = record["best_pole"]
    pole = nx.from_graph6_bytes(pole_data["graph6"].encode("ascii"))
    graph = glue((pole, pole_data["terminals"]), (nx.cycle_graph(PORTS), list(range(PORTS))), permutation)
    edges, cnf = encode(graph)
    boundary = [i for i, (u, v) in enumerate(edges) if u < len(pole) <= v]
    assert len(boundary) == PORTS and nx.is_connected(graph)
    cover = search(graph, prefix)
    assert cover["status"] == "checked-cover"

    # At an odd pole each color uses an odd number of ports. If one
    # uses all five, each of the other colors uses exactly one.
    for color in range(6):
        cnf.append([-(1 + 6 * i + color) for i in boundary])

    with Glucose4(bootstrap_with=cnf.clauses, with_proof=True) as solver:
        if solver.solve():
            raise ValueError("The splice has a cover with no color using all five ports")
        proof = solver.get_proof()
    cnf.to_file(str(prefix.with_suffix(".cnf")))
    prefix.with_suffix(".drat").write_text("\n".join(proof) + "\n", encoding="ascii")
    return {"order": len(graph), "boundary": [edges[i] for i in boundary],
            "graph6": nx.to_graph6_bytes(graph, header=False).decode().strip(), **cover}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("prefix", type=Path)
    parser.add_argument("--permutation", nargs=PORTS, type=int, default=(0, 2, 4, 1, 3))
    args = parser.parse_args()
    if sorted(args.permutation) != list(range(PORTS)):
        parser.error("The port numbers must form a permutation of 0 through 4")
    best = json.loads(args.report.read_text(encoding="utf-8-sig").splitlines()[-1])
    print(json.dumps(certify(best, args.permutation, args.prefix)))
