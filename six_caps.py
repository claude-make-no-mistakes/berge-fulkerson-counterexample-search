"""Check six-port boundary conditions for a hexagon in a counterexample."""

from functools import cache
from itertools import combinations, permutations, product
import json

import networkx as nx

from five_cut import active_bits, relabel_type
from six_cut import boundary_types, cycle_control


TYPES = boundary_types()
VARIABLE = {shape: index for index, shape in enumerate(TYPES, 1)}
COLORS = tuple(combinations(range(6), 2))
PAIRS = tuple((1 << a) | (1 << b) for a, b in COLORS)
FULL = (1 << 6) - 1

# Each replacement specifies its internal edges, incident port sets, and bare wires.
CAPS = (
    ("three wires", (), (), ((0, 1), (2, 3), (4, 5))),
    ("two junctions", (), ((0, 1, 2), (3, 4, 5)), ()),
    ("edge and wire", ((0, 1),), ((0, 1), (2, 3)), ((4, 5),)),
    ("four-vertex star", ((0, 1), (0, 2), (0, 3)), ((), (0, 1), (2, 3), (4, 5)), ()),
    ("four-vertex path", ((0, 1), (1, 2), (2, 3)), ((0, 1), (2,), (3,), (4, 5)), ()),
    ("triangle and junction", ((0, 1), (0, 2), (1, 2)), ((0,), (1,), (2,), (3, 4, 5)), ()),
    ("double edge and two wires", ((0, 1), (0, 1)), ((0,), (1,)), ((2, 3), (4, 5))),
    ("square and wire", ((0, 1), (1, 2), (2, 3), (0, 3)), ((0,), (1,), (2,), (3,)), ((4, 5),)),
)


def port_labels(shape):
    return tuple(sum(1 << color for color, support in enumerate(shape) if support >> port & 1)
                 for port in range(6))


def accepts(labels, edges, ports, wires):
    if any(labels[a] != labels[b] for a, b in wires):
        return False
    used = [0] * len(ports)
    for v, group in enumerate(ports):
        for port in group:
            if used[v] & labels[port]:
                return False
            used[v] |= labels[port]

    def assign(i):
        if i == len(edges):
            return all(mask == FULL for mask in used)
        u, v = edges[i]
        for pair in PAIRS:
            if pair & (used[u] | used[v]):
                continue
            used[u] ^= pair
            used[v] ^= pair
            if assign(i + 1):
                return True
            used[u] ^= pair
            used[v] ^= pair
        return False

    return assign(0)


def caps_by_kind():
    for name, edges, ports, wires in CAPS:
        base = tuple(shape for shape in TYPES if accepts(port_labels(shape), edges, ports, wires))
        profiles = {tuple(sorted(VARIABLE[relabel_type(shape, order)] for shape in base))
                    for order in permutations(range(6))}
        yield name, profiles


@cache
def pairings(ports):
    if not ports:
        return ((),)
    first, *rest = ports
    return tuple(((1 << first) | (1 << other), *tail)
                 for i, other in enumerate(rest)
                 for tail in pairings(tuple(rest[:i] + rest[i + 1:])))


def possible_switches(shape, a, b, allowed, variable):
    ports = tuple(active_bits(shape[a] ^ shape[b]))
    for pairs in pairings(ports):
        # Switching all chains exchanges the names of the pair's two colors.
        # The subsets excluding the last chain suffice up to color renaming.
        deltas = {0}
        for ends in pairs[:-1]:
            deltas |= {delta | ends for delta in deltas}
        valid = True
        for delta in deltas - {0}:
            shifted = list(shape)
            shifted[a] ^= delta
            shifted[b] ^= delta
            if variable[tuple(sorted(shifted))] not in allowed:
                valid = False
                break
        if valid:
            yield tuple((a, b, delta) for delta in sorted(deltas))


def allows_color_pairing(shape, pairing, allowed, variable):
    choices = [tuple(possible_switches(shape, a, b, allowed, variable)) for a, b in pairing]
    for switches in product(*choices):
        for deltas in product(*switches):
            shifted = list(shape)
            for a, b, delta in deltas:
                shifted[a] ^= delta
                shifted[b] ^= delta
            if variable[tuple(sorted(shifted))] not in allowed:
                break
        else:
            return True
    return False


def simultaneous_closure(allowed, types=TYPES, partitions=None):
    if partitions is None:
        partitions = tuple(tuple(tuple(active_bits(pair)) for pair in grouping)
                           for grouping in pairings(tuple(range(6))))
    variable = {shape: v for v, shape in enumerate(types, 1)}
    sizes = [len(allowed)]
    while True:
        remaining = {v for v in allowed if all(allows_color_pairing(types[v - 1], pairing, allowed, variable)
                                               for pairing in partitions)}
        if remaining == allowed:
            return remaining, sizes
        allowed = remaining
        sizes.append(len(allowed))


def signed_profile(positive, defect_colors):
    """Allowed types for plus-side defects with the listed color multiplicities."""
    numerator = 2 * positive.bit_count() - 6 + sum(defect_colors)
    if numerator % 3:
        return set()
    balance = numerator // 3
    target = sorted(balance - 2 * times for times in defect_colors)
    negative = FULL ^ positive
    return {v for v, shape in enumerate(TYPES, 1)
            if sorted((support & positive).bit_count() - (support & negative).bit_count()
                      for support in shape) == target}


def wire_profiles():
    for pairs in pairings(tuple(range(6))):
        wires = tuple(tuple(active_bits(pair)) for pair in pairs)
        yield wires, {v for v, shape in enumerate(TYPES, 1) if accepts(port_labels(shape), (), (), wires)}


def representative(positive):
    return min(sum(1 << ((direction * i + shift) % 6) for i in active_bits(positive))
               for direction in (1, -1) for shift in range(6))


def signed_cases(hexagon):
    wires = tuple(wire_profiles())
    cases = (
        ("bipartite", (0, 0, 0, 0, 0, 0), (0, 3)),
        ("one defect", (0, 0, 0, 0, 1, 1), (2, 5)),
        ("two incident defects", (0, 0, 1, 1, 1, 1), (1, 4)),
    )
    for name, multiplicities, sizes in cases:
        for positive in range(1 << 6):
            if positive.bit_count() not in sizes or representative(positive) != positive:
                continue
            eligible = signed_profile(positive, multiplicities)
            allowed, counts = simultaneous_closure(eligible - hexagon)
            separating = [pairs for pairs, types in wires if allowed.isdisjoint(types)]
            if name == "bipartite":
                assert not allowed
            else:
                assert separating
            yield {"case": name, "positive_ports": list(active_bits(positive)),
                   "eligible": len(eligible), "closure_sizes": counts,
                   "disjoint_wire_caps": len(separating), "wire_witness": separating[0] if separating else None}

    # The two defects may be disjoint when the negative ports are opposite.
    # Union the type sets for all overlaps of the two defect labels before closure.
    positive = (1 << 0) | (1 << 1) | (1 << 3) | (1 << 4)
    eligible = set().union(*(signed_profile(positive, (0,) * (2 + overlap) +
                                           (1,) * (4 - 2 * overlap) + (2,) * overlap)
                              for overlap in range(3)))
    allowed, counts = simultaneous_closure(eligible - hexagon)
    separating = [pairs for pairs, types in wires if allowed.isdisjoint(types)]
    assert separating
    yield {"case": "two defects and opposite negative ports", "positive_ports": list(active_bits(positive)),
           "eligible": len(eligible), "closure_sizes": counts,
           "disjoint_wire_caps": len(separating), "wire_witness": separating[0]}


def three_color_cases():
    even = tuple(mask for mask in range(64) if mask.bit_count() % 2 == 0)
    types = tuple(sorted({tuple(sorted((a, b, FULL ^ a ^ b))) for a, b in product(even, repeat=2) if not a & b}))
    hexagon = set()
    for colors in product(range(3), repeat=6):
        if any(colors[i] == colors[i - 1] for i in range(6)):
            continue
        ports = [3 - colors[i] - colors[i - 1] for i in range(6)]
        hexagon.add(tuple(sorted(sum(1 << i for i, v in enumerate(ports) if v == c) for c in range(3))))
    partitions = tuple((pair,) for pair in combinations(range(3), 2))
    for positive in (7, 11, 21):
        eligible = {v for v, shape in enumerate(types, 1)
                    if all((mask & positive).bit_count() == (mask & (FULL ^ positive)).bit_count() for mask in shape)}
        initial = {v for v in eligible if types[v - 1] not in hexagon}
        remaining, counts = simultaneous_closure(initial, types, partitions)
        assert not remaining
        yield {"case": "balanced bipartite, three colors", "positive_ports": list(active_bits(positive)),
               "eligible": len(eligible), "closure_sizes": counts}


def main():
    hexagon = {VARIABLE[shape] for shape in cycle_control(nx.cycle_graph(6))}
    remaining, counts = simultaneous_closure(set(VARIABLE.values()) - hexagon)
    print(json.dumps({"case": "unrestricted", "eligible": len(TYPES), "hexagon_types": len(hexagon),
                      "closure_sizes": counts,
                      "caps": {name: {"orientations": len(profiles), "types": len(next(iter(profiles))),
                                      "contained_in_hexagon": sum(set(profile) <= hexagon for profile in profiles),
                                      "least_intersection": min(len(remaining.intersection(profile))
                                                                for profile in profiles)}
                               for name, profiles in caps_by_kind()}}), flush=True)
    for record in signed_cases(hexagon):
        print(json.dumps(record), flush=True)
    for record in three_color_cases():
        print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
