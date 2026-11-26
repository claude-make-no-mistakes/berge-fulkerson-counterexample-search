"""Compose exact boundary profiles by gluing two ports of two five-poles."""

import argparse
from collections import Counter, defaultdict
from functools import cache
from itertools import combinations, combinations_with_replacement, permutations
import json
from pathlib import Path

import networkx as nx

from cyclic_cut import small_cyclic_cut
from five_cut import TYPES as FIVE_TYPES, active_bits, boundary_profile, glue, relabel_type
from five_targets import COMPLEMENTARY_PAIR, PENTAGON, orientations as five_orientations
from narrow_poles import decode, encode
from search import search
from six_caps import TYPES as SIX_TYPES, port_labels


SIX_INDEX = {shape: i for i, shape in enumerate(SIX_TYPES)}
COLOR_PERMUTATIONS = tuple(permutations(range(6)))
CANONICAL_SEAMS = ((3, 12), (3, 5), (3, 3))


@cache
def remap_colors(source, target):
    """Color permutations realizing the required ordered seam labels."""
    if tuple(mask.bit_count() for mask in source) != (2, 2):
        raise ValueError("Expected two color pairs")
    result = []
    for perm in COLOR_PERMUTATIONS:
        def move(mask):
            return sum(1 << perm[c] for c in active_bits(mask))

        if tuple(move(mask) for mask in source) == target:
            result.append(tuple(move(mask) for mask in range(64)))
    return tuple(result)


@cache
def normalized_exits(profile, seam):
    outside = tuple(i for i in range(5) if i not in seam)
    exits = [set(), set(), set()]
    for i in active_bits(profile):
        labels = port_labels(FIVE_TYPES[i], 5)
        source = tuple(labels[j] for j in seam)
        count = (source[0] & source[1]).bit_count()
        for recolor in remap_colors(source, CANONICAL_SEAMS[count]):
            exits[count].add(tuple(recolor[labels[j]] for j in outside))
    return tuple(frozenset(group) for group in exits)


@cache
def joined_type_bit(left, right):
    labels = (*left, *right)
    shape = tuple(sorted(sum(1 << p for p, mask in enumerate(labels) if mask >> c & 1)
                         for c in range(6)))
    return 1 << SIX_INDEX[shape]


def compose_profile(left_profile, left_seam, right_profile, right_seam):
    profile = 0
    left_exits = normalized_exits(left_profile, left_seam)
    right_exits = normalized_exits(right_profile, right_seam)
    for left, right in zip(left_exits, right_exits, strict=True):
        for a in left:
            for b in right:
                profile |= joined_type_bit(a, b)
    return profile


def compose_pole(left, left_seam, right, right_seam):
    graph_a, ports_a = left
    graph_b, ports_b = right
    node_a = {v: i for i, v in enumerate(graph_a)}
    node_b = {v: i + len(graph_a) for i, v in enumerate(graph_b)}
    graph = glue((graph_a, tuple(ports_a[i] for i in left_seam)),
                 (graph_b, tuple(ports_b[i] for i in right_seam)), range(2))
    ports = tuple(node_a[p] for i, p in enumerate(ports_a) if i not in left_seam)
    ports += tuple(node_b[p] for i, p in enumerate(ports_b) if i not in right_seam)
    return graph, ports


def source(path):
    record = json.loads(path.read_text(encoding="utf-8-sig").splitlines()[-1])
    return decode(record["best_pole"] if "best_pole" in record else record["best"]["pole"])


def classified_four_poles():
    pentagons = set(five_orientations(PENTAGON))
    other = set().union(*(set(five_orientations(profile)) for profile in COMPLEMENTARY_PAIR))
    allowed = tuple(sorted(pentagons | other))
    halves = [(int(a in pentagons) + int(b in pentagons), compose_profile(a, (0, 1), b, (0, 1)))
              for a in allowed for b in allowed]
    # Two joins each between 0–1, 0–2, 2–3 and 1–3; one each between 0–3 and 1–2.
    port_order = (0, 1, 5, 3, 4, 2)
    table = tuple(1 << SIX_INDEX[relabel_type(shape, port_order)] for shape in SIX_TYPES)
    right_halves = [(count, sum(table[i] for i in active_bits(profile))) for count, profile in halves]
    counts = Counter()
    minima = {}
    for left_pentagons, left in halves:
        for right_pentagons, right in right_halves:
            pentagon_count = left_pentagons + right_pentagons
            size = (left & right).bit_count()
            counts[pentagon_count] += 1
            minima[pentagon_count] = min(minima.get(pentagon_count, size), size)
    assert min(minima.values()) > 0
    return {"profile_choices": len(allowed), "composed_choices_per_side": len(halves),
            "distinct_profiles_per_side": len({profile for _, profile in halves}),
            "configurations": sum(counts.values()), "minimum_common_types": min(minima.values()),
            "by_pentagon_count": [{"pentagons": k, "configurations": counts[k], "minimum_common_types": minima[k]}
                                  for k in sorted(counts)]}


def scan(poles, export):
    profiles = [boundary_profile(*pole) for pole in poles]
    seams = tuple(combinations(range(5), 2))
    compiled = defaultdict(list)
    for a, b in combinations_with_replacement(range(len(poles)), 2):
        for seam_a in seams:
            for seam_b in seams:
                for ordered_b in (seam_b, seam_b[::-1]):
                    mask = compose_profile(profiles[a], seam_a, profiles[b], ordered_b)
                    compiled[mask].append((a, seam_a, b, ordered_b))

    for mask in sorted(compiled, key=int.bit_count)[:3]:
        a, seam_a, b, seam_b = compiled[mask][0]
        pole = compose_pole(poles[a], seam_a, poles[b], seam_b)
        assert boundary_profile(*pole, SIX_TYPES) == mask

    maps = tuple(tuple(1 << SIX_INDEX[relabel_type(shape, order)] for shape in SIX_TYPES)
                 for order in COLOR_PERMUTATIONS)
    candidates = sorted(compiled, key=lambda mask: (mask.bit_count(), mask))
    best = len(SIX_TYPES)
    tested = disjoint = rejected = 0
    witness = None

    def summary():
        return {"source_poles": [encode(*pole) for pole in poles],
                "source_profile_sizes": [profile.bit_count() for profile in profiles],
                "compositions": sum(map(len, compiled.values())), "distinct_profiles": len(compiled),
                "smallest_profile": candidates[0].bit_count(), "profile_alignments_tested": tested,
                "minimum_common_types": best, "disjoint_profile_alignments": disjoint,
                "cyclic_rejections": rejected, "witness": witness}

    for right_index, right in enumerate(candidates):
        active = tuple(active_bits(right))
        orientations = defaultdict(list)
        for order, table in zip(COLOR_PERMUTATIONS, maps, strict=True):
            orientations[sum(table[i] for i in active)].append(order)
        for left in candidates[:right_index + 1]:
            for oriented, orders in orientations.items():
                tested += 1
                common = (left & oriented).bit_count()
                best = min(best, common)
                if common:
                    continue
                disjoint += 1
                for a, seam_a, b, seam_b in compiled[left]:
                    left_pole = compose_pole(poles[a], seam_a, poles[b], seam_b)
                    for c, seam_c, d, seam_d in compiled[right]:
                        right_pole = compose_pole(poles[c], seam_c, poles[d], seam_d)
                        for order in orders:
                            graph = glue(left_pole, right_pole, order)
                            if list(nx.bridges(graph)) or small_cyclic_cut(graph) is not None:
                                rejected += 1
                                continue
                            result = search(graph, export)
                            if result["status"] != "unsat-awaiting-proof-check":
                                raise RuntimeError("Profile composition disagrees with the graph verifier")
                            witness = {"graph6": nx.to_graph6_bytes(graph, header=False).decode().strip(), **result}
                            return summary()

    return summary()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("poles", type=Path, nargs="*")
    parser.add_argument("--classified-four-cuts", action="store_true")
    parser.add_argument("--proof-prefix", type=Path, default=Path("composed-six-pole-witness"))
    args = parser.parse_args()
    if args.classified_four_cuts:
        if args.poles:
            parser.error("The four-cut replay uses the classified profiles")
        print(json.dumps(classified_four_poles()), flush=True)
    else:
        print(json.dumps(scan([(nx.cycle_graph(5), tuple(range(5))), *map(source, args.poles)], args.proof_prefix)), flush=True)
