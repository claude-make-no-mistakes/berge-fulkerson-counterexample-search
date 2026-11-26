"""Search five-poles for the exact profiles of a minimal counterexample."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
from random import Random

import networkx as nx

from cyclic_cut import small_cyclic_cut
from five_cut import PORTS, boundary_profile, cycle_poles, glue
from five_targets import nearest_target, orientations, targets
from narrow_poles import admits_bridgeless_splice, decode, edge_switch, encode, move_terminal
from search import search


def read_restart(path):
    record = json.loads(path.read_text(encoding="utf-8-sig").splitlines()[-1])
    return decode(record["best_pole"] if "best_pole" in record else record["best"]["pole"])


def scan(sources, restarts, trials, seed, prefix, pentagon_cyclic_five=False):
    rng = Random(seed)
    visited = set()
    elite = {}
    exact = defaultdict(list)
    best = None
    counts = {"seeds": 0, "mutations": 0, "scored": 0}
    pentagon = nx.cycle_graph(PORTS), tuple(range(PORTS))
    pentagon_orders = orientations(boundary_profile(*pentagon))
    pentagon_targets = {mask: [] for mask in pentagon_orders}
    for candidate, partners in targets().items():
        for case, partner in partners:
            if case < 13:
                pentagon_targets[partner].append(candidate)
    for mask, order in pentagon_orders.items():
        exact[mask].append((pentagon[0], tuple(pentagon[1][order.index(j)] for j in range(PORTS))))

    def pentagon_rank(graph, ports, profile):
        def distance(mask):
            return (profile ^ mask).bit_count(), (profile & ~mask).bit_count(), mask

        choices = sorted((min(map(distance, candidates)), partner)
                         for partner, candidates in pentagon_targets.items())
        for rank, partner in choices:
            joined = glue((graph, ports), pentagon, pentagon_orders[partner])
            if small_cyclic_cut(joined) is None:
                return rank, partner
        return None

    def evaluate(graph, ports, kind):
        nonlocal best
        data = encode(graph, ports)
        signature = data["graph6"], tuple(data["terminals"])
        if signature in visited or not admits_bridgeless_splice(graph, ports):
            return None
        visited.add(signature)
        counts[kind] += 1
        profile = boundary_profile(graph, ports)
        if pentagon_cyclic_five:
            result = pentagon_rank(graph, ports, profile)
            if result is None:
                return None
            rank, partner = result
        else:
            rank, partner = nearest_target(profile), None
        counts["scored"] += 1
        canonical = min(orientations(profile))
        elite[canonical] = min(elite.get(canonical, (rank, signature, graph, ports)),
                               (rank, signature, graph, ports), key=lambda record: record[:2])
        if best is None or rank < tuple(best["rank"]):
            best = {"rank": rank, "profile": f"{profile:014x}",
                    "target": f"{rank[2]:014x}", "cases": sorted({case for case, _ in targets()[rank[2]]}),
                    "pole": data}
            if partner is not None:
                best["pentagon_profile"] = f"{partner:014x}"
                best["common_types"] = (profile & partner).bit_count()
        for mask, order in orientations(profile).items():
            if mask not in targets():
                continue
            ordered_ports = tuple(ports[order.index(j)] for j in range(PORTS))
            pole = graph, ordered_ports
            for case, partner in sorted(targets()[mask]):
                if pentagon_cyclic_five and case == 13:
                    continue
                for other in exact[partner]:
                    joined = glue(pole, other, range(PORTS))
                    if any(nx.bridges(joined)) or small_cyclic_cut(joined) is not None:
                        continue
                    certificate = search(joined, prefix)
                    assert certificate["status"] == "unsat-awaiting-proof-check"
                    return {"case": case, "graph6": nx.to_graph6_bytes(joined, header=False).decode().strip(),
                            "proof": certificate}
            exact[mask].append(pole)
        return None

    seeds = [pole for graph in sources for pole in cycle_poles(graph)] + restarts
    for graph, ports in seeds:
        witness = evaluate(graph, ports, "seeds")
        if witness is not None:
            return {**counts, "best": best, "witness": witness}
    if not elite:
        raise ValueError("No usable seed five-poles")
    for _ in range(4 * trials):
        if counts["mutations"] == trials:
            break
        ordered = sorted(elite.values(), key=lambda record: record[:2])
        pool = ordered[:20] if rng.randrange(4) else ordered
        _, _, graph, ports = rng.choice(pool)
        if rng.randrange(3) == 0:
            moved = move_terminal(graph, ports, rng)
            if moved is None:
                continue
            changed, ports = moved
        else:
            changed = edge_switch(graph, rng)
            if changed is None:
                continue
        witness = evaluate(changed, ports, "mutations")
        if witness is not None:
            return {**counts, "best": best, "witness": witness}
    return {"seed": seed, **counts, "pentagon_cyclic_five": pentagon_cyclic_five,
            "distinct_profiles_up_to_relabeling": len(elite),
            "exact_target_masks": sum(mask in targets() for mask in exact if exact[mask]),
            "best": best, "witness": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--restart", action="append", type=Path, default=[])
    parser.add_argument("--trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20261209)
    parser.add_argument("--pentagon-cyclic-five", action="store_true",
                        help="Score only pentagon attachments without smaller cyclic cuts")
    parser.add_argument("--proof-prefix", type=Path, default=Path("target-five-witness"))
    args = parser.parse_args()
    if args.trials < 0:
        parser.error("Expected a nonnegative trial count")
    graphs = [nx.from_graph6_bytes(row) for row in args.corpus.read_bytes().splitlines()]
    restarts = [read_restart(path) for path in args.restart]
    print(json.dumps(scan(graphs, restarts, args.trials, args.seed, args.proof_prefix, args.pentagon_cyclic_five)),
          flush=True)
