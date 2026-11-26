"""Search for Berge–Fulkerson obstructions by exact five-pole boundary profiles."""

import argparse
from collections import Counter
from itertools import combinations, combinations_with_replacement, permutations
import json
from pathlib import Path

import networkx as nx
from pysat.formula import CNF
from pysat.solvers import Glucose4

from search import exact_count, search
from splice import five_poles


PORTS = 5
MASK = (1 << PORTS) - 1
SINGLETONS = tuple(1 << i for i in range(PORTS))


def boundary_types():
    """Each color meets the odd pole in one, three, or five semiedges."""
    types = {tuple(sorted((MASK, *SINGLETONS)))}
    heavy = [MASK ^ a ^ b for a, b in combinations(SINGLETONS, 2)]
    for x, y in combinations_with_replacement(heavy, 2):
        light = [bit for bit in SINGLETONS for _ in range(2 - bool(x & bit) - bool(y & bit))]
        types.add(tuple(sorted((x, y, *light))))
    assert len(types) == 56  # Section 4 of Máčajová, Mazzuoccolo and Tabarelli.
    return tuple(sorted(types))


TYPES = boundary_types()


def boundary_profile(pole, terminals, types=TYPES):
    """Return a bit per realizable boundary type, with the given terminal ordering."""
    arity = len(terminals)
    if len(pole) % 2 != arity % 2 or len(set(terminals)) != arity:
        raise ValueError("Expected distinct terminal vertices and an order with the same parity as the cut")
    internal = list(pole.edges())
    incident = {vertex: [] for vertex in pole}
    for index, (u, v) in enumerate(internal):
        incident[u].append(index)
        incident[v].append(index)
    for i, vertex in enumerate(terminals, len(internal)):
        incident[vertex].append(i)
    if any(len(edges) != 3 for edges in incident.values()):
        raise ValueError("Every pole vertex must have three incident edges, counting semiedges")

    def variable(edge, color):
        return 1 + 6 * edge + color

    cnf = CNF()
    for index in range(len(internal) + arity):
        cnf.extend(exact_count([variable(index, color) for color in range(6)], 2))
    for edges in incident.values():
        for color in range(6):
            cnf.extend(exact_count([variable(index, color) for index in edges], 1))

    profile = 0
    with Glucose4(bootstrap_with=cnf.clauses) as solver:
        for i, shape in enumerate(types):
            assumptions = [variable(len(internal) + port, color) for color, mask in enumerate(shape)
                           for port in range(arity) if mask >> port & 1]
            if not solver.solve(assumptions=assumptions):
                continue
            model = {v for v in solver.get_model() if v > 0}
            edge_colors = [tuple(color for color in range(6) if variable(edge, color) in model)
                           for edge in range(len(internal) + arity)]
            assert all(len(colors) == 2 for colors in edge_colors)
            assert all(sorted(color for edge in edges for color in edge_colors[edge]) == list(range(6))
                       for edges in incident.values())
            assert all(edge_colors[len(internal) + j] == tuple(c for c, mask in enumerate(shape) if mask >> j & 1)
                       for j in range(arity))
            profile |= 1 << i
    return profile


def relabel_type(shape, permutation):
    return tuple(sorted(sum(1 << new for old, new in enumerate(permutation) if mask >> old & 1) for mask in shape))


def active_bits(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def cycle_poles(graph, arity=PORTS):
    cycles = {tuple(sorted(cycle)) for cycle in nx.simple_cycles(graph, length_bound=arity) if len(cycle) == arity}
    for cycle in sorted(cycles):
        if graph.subgraph(cycle).number_of_edges() != arity:
            continue
        terminals = sorted(v for u in cycle for v in graph[u] if v not in cycle)
        remainder = graph.copy()
        remainder.remove_nodes_from(cycle)
        if len(terminals) == len(set(terminals)) == arity and nx.is_connected(remainder):
            yield remainder, terminals


def glue(left, right, permutation):
    a, a_terminals = left
    b, b_terminals = right
    a_map = {vertex: i for i, vertex in enumerate(a)}
    b_map = {vertex: i + len(a) for i, vertex in enumerate(b)}
    joined = nx.compose(nx.relabel_nodes(a, a_map), nx.relabel_nodes(b, b_map))
    joined.add_edges_from((a_map[a_terminals[j]], b_map[b_terminals[i]]) for i, j in enumerate(permutation))
    return joined


def validate():
    # On a 5-cycle a color meeting three semiedges must use the edge joining the other two vertices.
    cycle = nx.cycle_graph(PORTS)
    adjacent = {MASK ^ (1 << u) ^ (1 << v) for u, v in cycle.edges()}
    expected = sum(1 << i for i, shape in enumerate(TYPES)
                   if MASK in shape or all(mask.bit_count() == 1 or mask in adjacent for mask in shape))
    assert expected.bit_count() == 16
    assert boundary_profile(cycle, list(range(PORTS))) == expected
    return expected


def compare_joinings(profiles, types, arity, export):
    port_permutations = list(permutations(range(arity)))
    positions = {shape: i for i, shape in enumerate(types)}
    map_bit = [{1 << i: 1 << j for i, j in enumerate((positions[relabel_type(shape, perm)] for shape in types))}
               for perm in port_permutations]
    ordered_joinings = sum(map(len, profiles.values()))**2 * len(port_permutations)
    disjoint_joinings = 0
    rejected_bridges = 0
    for b_profile, right_poles in profiles.items():
        eligible = [(a_profile, left_poles) for a_profile, left_poles in profiles.items()
                    if a_profile.bit_count() + b_profile.bit_count() <= len(types)]
        if not eligible:
            continue
        bits = tuple(1 << i for i in active_bits(b_profile))
        for permutation, mapping in zip(port_permutations, map_bit, strict=True):
            remapped = sum(mapping[bit] for bit in bits)
            for a_profile, left_poles in eligible:
                pair_count = len(left_poles) * len(right_poles)
                if a_profile & remapped:
                    continue
                disjoint_joinings += pair_count
                for left in left_poles:
                    for right in right_poles:
                        graph = glue(left, right, permutation)
                        if any(nx.bridges(graph)):
                            rejected_bridges += 1
                            continue
                        result = search(graph, export)
                        assert result["status"] == "unsat-awaiting-proof-check", "Profile scan and full solver disagree"
                        return {"candidate_graph6": nx.to_graph6_bytes(graph, header=False).decode().strip(),
                                "proof": result}
    sizes = Counter()
    for profile, poles in profiles.items():
        sizes[profile.bit_count()] += len(poles)
    return {"profile_size_distribution": dict(sorted(sizes.items())),
            "distinct_ordered_profiles": len(profiles), "ordered_joinings": ordered_joinings,
            "disjoint_profile_joinings": disjoint_joinings, "bridge_rejections": rejected_bridges, "witness": None}


def scan(sources, path_limit, export):
    cycle = nx.cycle_graph(PORTS), list(range(PORTS))
    profiles = {validate(): [cycle]}
    counts = Counter(pentagons=1)
    for graph in sources:
        for kind, candidates in (("cycle_complements", list(cycle_poles(graph))),
                                 ("path_complements", list(five_poles(graph))[:path_limit])):
            for pole, terminals in candidates:
                profile = boundary_profile(pole, terminals)
                profiles.setdefault(profile, []).append((pole, terminals))
                counts[kind] += 1
    return {"poles_by_kind": dict(counts), **compare_joinings(profiles, TYPES, PORTS, export)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--path-limit", type=int, default=12)
    parser.add_argument("--proof-prefix", type=Path, default=Path("five-cut-witness"))
    args = parser.parse_args()
    if args.path_limit < 0:
        parser.error("Expected --path-limit to be nonnegative")
    graphs = [nx.from_graph6_bytes(line) for line in args.corpus.read_bytes().splitlines()]
    print(json.dumps(scan(graphs, args.path_limit, args.proof_prefix)))


if __name__ == "__main__":
    main()
