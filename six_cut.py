"""Check six-edge splices for incompatible Berge–Fulkerson boundary profiles."""

import argparse
from collections import Counter
from itertools import combinations_with_replacement
import json
from pathlib import Path

import networkx as nx

from five_cut import active_bits, boundary_profile, compare_joinings, cycle_poles


PORTS = 6
MASK = (1 << PORTS) - 1


def boundary_types():
    # Each color meets an even fragment in an even number of semiedges.
    masks = tuple(mask for mask in range(1 << PORTS) if mask.bit_count() % 2 == 0)

    def visit(usage, count, start):
        if count == 0:
            if not any(usage):
                yield ()
            return
        for i in range(start, len(masks)):
            mask = masks[i]
            remaining = tuple(slots - (mask >> port & 1) for port, slots in enumerate(usage))
            if min(remaining) >= 0 and max(remaining) < count:
                for other_colors in visit(remaining, count - 1, i):
                    yield (mask, *other_colors)

    return tuple(visit((2,) * PORTS, 6, 0))


def cycle_control(cycle):
    """Independent enumeration of single-color matchings and their six-fold multiset covers."""
    edges = list(cycle.edges())
    matchings = []
    for bits in range(1 << len(edges)):
        pairs = [v for i in active_bits(bits) for v in edges[i]]
        if len(pairs) == len(set(pairs)):
            mask = MASK ^ sum(1 << v for v in pairs)
            matchings.append((bits, mask))
    profiles = set()
    for pick in combinations_with_replacement(matchings, 6):
        if all(sum(edge_mask >> i & 1 for edge_mask, _ in pick) == 2 for i in range(len(edges))):
            profiles.add(tuple(sorted(boundary for _, boundary in pick)))
    return profiles


def scan(sources, cap_per_graph, export):
    types = boundary_types()
    cycle = nx.cycle_graph(PORTS)
    terminals = list(range(PORTS))
    expected = cycle_control(cycle)
    actual = boundary_profile(cycle, terminals, types)
    assert {types[i] for i in active_bits(actual)} == expected
    profiles = {actual: [(cycle, terminals)]}
    counts = Counter(hexagons=1)
    for graph in sources:
        for pole, terminals in list(cycle_poles(graph, arity=PORTS))[:cap_per_graph]:
            mask = boundary_profile(pole, terminals, types)
            profiles.setdefault(mask, []).append((pole, terminals))
            counts["cycle_complements"] += 1
    return {"boundary_types": len(types), "hexagon_types": len(expected), "poles_by_kind": dict(counts),
            **compare_joinings(profiles, types, PORTS, export)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--cap-per-graph", type=int, default=16)
    parser.add_argument("--proof-prefix", type=Path, default=Path("six-cut-witness"))
    args = parser.parse_args()
    if args.cap_per_graph < 0:
        parser.error("Expected --cap-per-graph to be nonnegative")
    graphs = [nx.from_graph6_bytes(line) for line in args.corpus.read_bytes().splitlines()]
    print(json.dumps(scan(graphs, args.cap_per_graph, args.proof_prefix)), flush=True)
