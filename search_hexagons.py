"""Search for hexagon splices with no compatible Berge–Fulkerson boundary type."""

import argparse
from collections import Counter
import json
from pathlib import Path
from random import Random

import networkx as nx

from cyclic_cut import small_cyclic_cut
from five_cut import boundary_profile, cycle_poles, glue
from narrow_poles import edge_switch, encode, move_terminal
from search import search
from six_cut import cycle_control


def run(graphs, trials, seed, proof_prefix, min_order=0):
    rng = Random(seed)
    hexagon = nx.cycle_graph(6)
    cap = hexagon, tuple(hexagon)
    types = tuple(sorted(cycle_control(hexagon)))
    counts = Counter(seeds=0, evaluated=0, cyclic_rejections=0, duplicate_rejections=0)
    profile_sizes = Counter()
    visited = set()
    elite = []
    best = None

    def evaluate(pole, terminals):
        nonlocal best
        data = encode(pole, terminals)
        key = data["graph6"], tuple(data["terminals"])
        if key in visited:
            counts["duplicate_rejections"] += 1
            return None
        visited.add(key)
        joined = glue((pole, terminals), cap, range(6))
        if list(nx.bridges(joined)) or small_cyclic_cut(joined) is not None:
            counts["cyclic_rejections"] += 1
            return None
        profile = boundary_profile(pole, terminals, types)
        total = profile.bit_count()
        counts["evaluated"] += 1
        profile_sizes[total] += 1
        if best is None or total < best["common_types"]:
            best = {"common_types": total, "pole": data, "profile": format(profile, "x"),
                    "joined_graph6": nx.to_graph6_bytes(joined, header=False).decode().strip()}
        if total == 0:
            result = search(joined, proof_prefix)
            if result["status"] != "unsat-awaiting-proof-check":
                raise RuntimeError("The full graph solver and boundary test disagree")
            return result
        elite.append((total, key, pole, terminals))
        elite.sort(key=lambda record: record[:2])
        del elite[30:]
        return None

    witness = None
    for graph in graphs:
        if len(graph) < min_order:
            continue
        for pole, terminals in cycle_poles(graph, arity=6):
            counts["seeds"] += 1
            trial_terminals = list(terminals)
            rng.shuffle(trial_terminals)
            witness = evaluate(pole, trial_terminals)
            if witness is not None:
                break
        if witness is not None:
            break
    if witness is None and not elite:
        raise ValueError("No eligible seed hexagon complement")
    for _ in range(trials):
        if witness is not None:
            break
        _, _, pole, terminals = rng.choice(elite)
        branch = rng.randrange(3)
        if branch == 0:
            changed = edge_switch(pole, rng)
            candidate = None if changed is None else (changed, terminals)
        elif branch == 1:
            candidate = move_terminal(pole, terminals, rng)
        else:
            ports = list(terminals)
            a, b = rng.sample(range(6), 2)
            ports[a], ports[b] = ports[b], ports[a]
            candidate = pole, ports
        if candidate is not None:
            witness = evaluate(*candidate)
    return {**counts, "trials": trials, "seed": seed, "min_order": min_order,
            "common_type_counts": dict(sorted(profile_sizes.items())),
            "best": best, "witness": witness}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--trials", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20261214)
    parser.add_argument("--min-order", type=int, default=0)
    parser.add_argument("--proof-prefix", type=Path, default=Path("hexagon-witness"))
    args = parser.parse_args()
    if args.trials < 0 or args.min_order < 0:
        parser.error("Expected nonnegative trial and order bounds")
    graphs = [nx.from_graph6_bytes(line) for line in args.corpus.read_bytes().splitlines() if line.strip()]
    print(json.dumps(run(graphs, args.trials, args.seed, args.proof_prefix, args.min_order)), flush=True)
