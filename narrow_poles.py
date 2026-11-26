"""Search for a pentagon splice with no compatible Berge–Fulkerson color type."""

import argparse
from collections import Counter
import json
from itertools import permutations
from pathlib import Path
from random import Random

import networkx as nx

from cyclic_cut import small_cyclic_cut
from five_cut import MASK, PORTS, TYPES, active_bits, boundary_profile, cycle_poles, glue, relabel_type, validate
from search import search


def pentagon_orientations():
    variants = profile_orientations(validate())
    assert len(variants) == 12  # Unoriented cycles on five labeled ports.
    return variants


def profile_orientations(profile):
    positions = {shape: i for i, shape in enumerate(TYPES)}
    variants = {}
    for perm in permutations(range(PORTS)):
        reordered = sum(1 << positions[relabel_type(TYPES[i], perm)] for i in active_bits(profile))
        variants.setdefault(reordered, perm)
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


def move_terminal(graph, terminals, rng):
    """Transfer one dangling edge by replacing an ordinary edge."""
    edges = list(graph.edges())
    for _ in range(200):
        slot = rng.randrange(len(terminals))
        old = terminals[slot]
        u, new = rng.choice(edges)
        if rng.randrange(2):
            new, u = u, new
        if new in terminals or u == old or graph.has_edge(u, old):
            continue
        changed = graph.copy()
        changed.remove_edge(u, new)
        if old in nx.single_source_shortest_path_length(changed, u, cutoff=3):
            continue
        changed.add_edge(u, old)
        if nx.is_connected(changed):
            moved = list(terminals)
            moved[slot] = new
            return changed, moved
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


def decode(pole_data):
    return nx.from_graph6_bytes(pole_data["graph6"].encode("ascii")), pole_data["terminals"]


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


def scan(sources, trials, seed, export, restart=None, avoid_all_ports=False, target=None, cyclic_five=False,
         terminal_moves=False):
    if target is None:
        target = nx.cycle_graph(PORTS), list(range(PORTS))
        orientations = pentagon_orientations()
    else:
        if not nx.is_connected(target[0]) or not admits_bridgeless_splice(*target):
            raise ValueError("The target must be a connected pole that can form a bridgeless splice")
        orientations = profile_orientations(boundary_profile(*target))
    all_ports = 1 << next(i for i, shape in enumerate(TYPES) if MASK in shape)

    def rank(pole, terminals, profile):
        if cyclic_five:
            ordered = sorted(orientations.items(), key=lambda pair: (pair[0] & profile).bit_count())
            for shape, permutation in ordered:
                joined = glue((pole, terminals), target, permutation)
                if small_cyclic_cut(joined) is None:
                    base = ((shape & profile).bit_count(), profile.bit_count())
                    break
            else:
                return None
        else:
            base = score(profile, orientations)
        # This type belongs to every orientation when the target admits it.
        return (bool(profile & all_ports), *base) if avoid_all_ports else base

    def candidate(pole, terminals, profile):
        for order, permutation in orientations.items():
            if profile & order:
                continue
            joined = glue((pole, terminals), target, permutation)
            if any(nx.bridges(joined)) or (cyclic_five and small_cyclic_cut(joined) is not None):
                continue
            outcome = search(joined, export)
            assert outcome["status"] == "unsat-awaiting-proof-check"
            return {"candidate_graph6": nx.to_graph6_bytes(joined, header=False).decode().strip(),
                    "pole": encode(pole, terminals), "proof": outcome}
        return None

    rng = Random(seed)
    pool = []
    recent = []
    seen = set()
    scores = Counter()
    bridge_rejections = 0
    cyclic_rejections = 0
    for graph in sources:
        poles = list(cycle_poles(graph))
        for pole, terminals in rng.sample(poles, min(3, len(poles))):
            profile = boundary_profile(pole, terminals)
            key = rank(pole, terminals, profile)
            if key is None:
                continue
            if key[-2] == 0:
                outcome = candidate(pole, terminals, profile)
                if outcome is not None:
                    return outcome
            pool.append((key, pole, terminals))
    if restart is not None:
        pole, terminals = decode(restart["best_pole"])
        if not admits_bridgeless_splice(pole, terminals):
            raise ValueError("The restart pole always produces a bridge")
        profile = boundary_profile(pole, terminals)
        key = rank(pole, terminals, profile)
        if key is not None:
            if key[-2] == 0:
                outcome = candidate(pole, terminals, profile)
                if outcome is not None:
                    return outcome
            pool.append((key, pole, terminals))
    if not pool:
        raise RuntimeError("No input graph yielded a pentagon complement")
    initial = min(key for key, _, _ in pool)
    without_all_ports = 0
    accepted_moves = 0
    for _ in range(trials * 4):
        if sum(scores.values()) == trials:
            break
        parents = recent if restart is not None and recent and rng.randrange(4) == 0 else pool
        _, graph, terminals = rng.choice(parents)
        transfer = terminal_moves and rng.randrange(3) == 0
        if transfer:
            moved = move_terminal(graph, terminals, rng)
            if moved is None:
                continue
            changed, terminals = moved
        else:
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
        key = rank(changed, terminals, profile)
        if key is None:
            cyclic_rejections += 1
            continue
        compatible = key[-2]
        scores[compatible] += 1
        accepted_moves += int(transfer)
        without_all_ports += not bool(profile & all_ports)
        if compatible == 0:
            outcome = candidate(changed, terminals, profile)
            if outcome is not None:
                return outcome
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
            "target_pole": encode(*target),
            "without_all_ports": without_all_ports,
            "terminal_moves": accepted_moves,
            "evaluated": sum(scores.values()), "minimum_common_type_histogram": dict(sorted(scores.items())),
            "bridge_rejections": bridge_rejections, "cyclic_rejections": cyclic_rejections, "witness": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--trials", type=int, default=600)
    parser.add_argument("--seed", type=int, default=20261127)
    parser.add_argument("--proof-prefix", type=Path, default=Path("pentagon-witness"))
    initial = parser.add_mutually_exclusive_group()
    initial.add_argument("--restart", type=Path)
    initial.add_argument("--bipartite-restart", type=int, metavar="HALF_ORDER")
    parser.add_argument("--target-pole", type=Path, help="Glue to the saved best pole instead of a pentagon")
    parser.add_argument("--cyclic-five", action="store_true", help="Only score pentagon splices with no smaller cyclic cut")
    parser.add_argument("--move-terminals", action="store_true", help="Also change which vertices carry the dangling edges")
    parser.add_argument("--avoid-all-ports", action="store_true",
                        help="Prefer profiles excluding any color that uses all five ports")
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("Expected a positive trial count")
    if args.bipartite_restart is not None and args.bipartite_restart < 9:
        parser.error("The bipartite seed requires at least nine vertices on each side")
    if args.cyclic_five and args.target_pole is not None:
        parser.error("Cyclic cut filtering uses pentagon attachments")
    graphs = [nx.from_graph6_bytes(line) for line in args.corpus.read_bytes().splitlines()]
    restart = json.loads(args.restart.read_text(encoding="utf-8-sig").splitlines()[-1]) if args.restart else None
    if args.bipartite_restart is not None:
        restart = bipartite_restart(args.bipartite_restart)
    target = None
    if args.target_pole is not None:
        target_record = json.loads(args.target_pole.read_text(encoding="utf-8-sig").splitlines()[-1])
        target = decode(target_record["best_pole"])
    result = scan(graphs, args.trials, args.seed, args.proof_prefix, restart, args.avoid_all_ports, target, args.cyclic_five,
                  args.move_terminals)
    print(json.dumps(result), flush=True)
