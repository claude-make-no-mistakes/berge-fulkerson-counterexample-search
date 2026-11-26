"""Search for a pentagon splice with no compatible Berge–Fulkerson color type."""

import argparse
from collections import Counter
import json
from itertools import permutations
from pathlib import Path
from random import Random

import networkx as nx

from five_cut import MASK, PORTS, TYPES, active_bits, boundary_profile, cycle_poles, glue, relabel_type, validate
from search import search


def pentagon_orientations():
    cycle_profile = validate()
    positions = {shape: i for i, shape in enumerate(TYPES)}
    variants = {}
    for perm in permutations(range(PORTS)):
        reordered = sum(1 << positions[relabel_type(TYPES[i], perm)] for i in active_bits(cycle_profile))
        variants.setdefault(reordered, perm)
    assert len(variants) == 12  # Unoriented cycles on five labeled ports.
    return variants


def edge_switch(graph, rng):
    edges = list(graph.edges())
    for _ in range(200):
        (a, b), (c, d) = rng.sample(edges, 2)
        if len({a, b, c, d}) != 4:
            continue
        if rng.randrange(2):
            c, d = d, c
        if graph.has_edge(a, c) or graph.has_edge(b, d):
            continue
        changed = graph.copy()
        changed.remove_edges_from(((a, b), (c, d)))
        changed.add_edges_from(((a, c), (b, d)))
        if not nx.is_connected(changed):
            continue
        no_short_cycles = True
        for u, v in ((a, c), (b, d)):
            changed.remove_edge(u, v)
            no_short_cycles &= v not in nx.single_source_shortest_path_length(changed, u, cutoff=3)
            changed.add_edge(u, v)
        if no_short_cycles:
            return changed
    return None


def score(profile, orientations):
    best = min((profile & shape).bit_count() for shape in orientations)
    return best, profile.bit_count()


def admits_bridgeless_splice(pole, terminals):
    # Contracting the pentagon preserves bridge status outside the pentagon itself.
    graph = pole.copy()
    contracted = object()
    graph.add_edges_from((contracted, vertex) for vertex in terminals)
    return not any(nx.bridges(graph))


def encode(pole, terminals):
    labels = {vertex: index for index, vertex in enumerate(pole)}
    return {"graph6": nx.to_graph6_bytes(pole, header=False).decode().strip(),
            "terminals": [labels[v] for v in terminals]}


def bipartite_restart(half_order):
    """Delete a three-vertex path from a cubic bipartite graph without 4-cycles."""
    graph = nx.Graph()
    graph.add_nodes_from(range(2 * half_order))
    graph.add_edges_from((u, half_order + (u + shift) % half_order)
                         for u in range(half_order) for shift in (0, 1, 4))
    path = {0, half_order, half_order + 1}
    terminals = sorted(v for u in path for v in graph[u] if v not in path)
    graph.remove_nodes_from(path)
    assert len(set(terminals)) == len(terminals) == PORTS and nx.is_connected(graph)
    profile = boundary_profile(graph, terminals)
    assert not any(MASK in TYPES[i] for i in active_bits(profile))
    return {"best_score": list(score(profile, pentagon_orientations())), "best_pole": encode(graph, terminals)}


def scan(sources, trials, seed, export, restart=None, avoid_all_ports=False):
    orientations = pentagon_orientations()
    cycle = nx.cycle_graph(PORTS), list(range(PORTS))
    all_ports = 1 << next(i for i, shape in enumerate(TYPES) if MASK in shape)

    def rank(profile):
        base = score(profile, orientations)
        # This type belongs to every pentagon orientation and must disappear.
        return (bool(profile & all_ports), *base) if avoid_all_ports else base

    rng = Random(seed)
    pool = []
    recent = []
    seen = set()
    scores = Counter()
    bridge_rejections = 0
    for graph in sources:
        poles = list(cycle_poles(graph))
        for pole, terminals in rng.sample(poles, min(3, len(poles))):
            profile = boundary_profile(pole, terminals)
            pool.append((rank(profile), pole, terminals))
    if restart is not None:
        best = restart["best_pole"]
        pole = nx.from_graph6_bytes(best["graph6"].encode("ascii"))
        terminals = best["terminals"]
        if not admits_bridgeless_splice(pole, terminals):
            raise ValueError("The restart pole always produces a bridge")
        profile = boundary_profile(pole, terminals)
        assert list(score(profile, orientations)) == restart["best_score"]
        pool.append((rank(profile), pole, terminals))
    if not pool:
        raise RuntimeError("No input graph yielded a pentagon complement")
    initial = min(key for key, _, _ in pool)
    without_all_ports = 0
    for _ in range(trials * 4):
        if sum(scores.values()) == trials:
            break
        parents = recent if restart is not None and recent and rng.randrange(4) == 0 else pool
        _, graph, terminals = rng.choice(parents)
        changed = edge_switch(graph, rng)
        if changed is None:
            continue
        if restart is not None and rng.randrange(3) == 0:
            alternate = edge_switch(changed, rng)
            if alternate is not None:
                changed = alternate
        if not admits_bridgeless_splice(changed, terminals):
            bridge_rejections += 1
            continue
        form = encode(changed, terminals)
        signature = form["graph6"], tuple(form["terminals"])
        if signature in seen:
            continue
        seen.add(signature)
        profile = boundary_profile(changed, terminals)
        compatible, _ = score(profile, orientations)
        key = rank(profile)
        scores[compatible] += 1
        without_all_ports += not bool(profile & all_ports)
        if compatible == 0:
            for order, perm in orientations.items():
                if profile & order:
                    continue
                joined = glue((changed, terminals), cycle, perm)
                if any(nx.bridges(joined)):
                    continue
                outcome = search(joined, export)
                assert outcome["status"] == "unsat-awaiting-proof-check"
                return {"candidate_graph6": nx.to_graph6_bytes(joined, header=False).decode().strip(),
                        "pole": form, "proof": outcome}
        pool.append((key, changed, terminals))
        pool.sort(key=lambda record: record[0])
        del pool[20:]
        recent.append((key, changed, terminals))
        del recent[:-12]
        if sum(scores.values()) % 500 == 0:
            print(json.dumps({"evaluated": sum(scores.values()), "current_best_score": pool[0][0][-2:],
                              "without_all_ports": without_all_ports}), flush=True)
    best_key, pole, terminals = min(pool, key=lambda record: record[0])
    return {"seed": seed, "initial_score": initial[-2:], "best_score": best_key[-2:],
            "best_pole": encode(pole, terminals), "avoid_all_ports": avoid_all_ports,
            "without_all_ports": without_all_ports,
            "evaluated": sum(scores.values()), "minimum_common_type_histogram": dict(sorted(scores.items())),
            "bridge_rejections": bridge_rejections, "witness": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--trials", type=int, default=600)
    parser.add_argument("--seed", type=int, default=20261127)
    parser.add_argument("--proof-prefix", type=Path, default=Path("pentagon-witness"))
    initial = parser.add_mutually_exclusive_group()
    initial.add_argument("--restart", type=Path)
    initial.add_argument("--bipartite-restart", type=int, metavar="HALF_ORDER")
    parser.add_argument("--avoid-all-ports", action="store_true",
                        help="Prefer profiles excluding any color that uses all five ports")
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("Expected a positive trial count")
    if args.bipartite_restart is not None and args.bipartite_restart < 9:
        parser.error("The bipartite seed requires at least nine vertices on each side")
    graphs = [nx.from_graph6_bytes(line) for line in args.corpus.read_bytes().splitlines()]
    restart = json.loads(args.restart.read_text(encoding="utf-8-sig").splitlines()[-1]) if args.restart else None
    if args.bipartite_restart is not None:
        restart = bipartite_restart(args.bipartite_restart)
    print(json.dumps(scan(graphs, args.trials, args.seed, args.proof_prefix, restart, args.avoid_all_ports)), flush=True)
