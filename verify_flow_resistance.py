"""Replay the Berge–Fulkerson covers of Mattiolo–Negrini–Pagani's H_n.

Figures 1–6 of https://arxiv.org/pdf/2604.22501 supply the graph construction.
Only the Python 3.10 standard library is required.
"""

import argparse
from collections import Counter
from dataclasses import dataclass
from functools import cache
from itertools import combinations, combinations_with_replacement, product
import json


COLORS = range(6)
ALL_COLORS = (1 << len(COLORS)) - 1
PAIRS = tuple((1 << a) | (1 << b) for a, b in combinations(COLORS, 2))
PAIR_SET = frozenset(PAIRS)
PETERSEN_EDGES = (
    (0, 1), (0, 4), (0, 5), (1, 2), (1, 6), (2, 3), (2, 7), (3, 4),
    (3, 8), (4, 9), (5, 7), (5, 8), (6, 8), (6, 9), (7, 9),
)


def edge(u, v):
    return tuple(sorted((u, v)))


@dataclass(frozen=True)
class Pole:
    edges: tuple[tuple[str, str], ...]
    ports: tuple[str, ...]

    def prefixed(self, prefix):
        return Pole(
            tuple((prefix + u, prefix + v) for u, v in self.edges),
            tuple(prefix + vertex for vertex in self.ports),
        )


def petersen_fragment(removed_vertices, cut_edge, ports):
    return Pole(
        tuple((str(u), str(v)) for u, v in PETERSEN_EDGES
              if u not in removed_vertices and v not in removed_vertices and (u, v) != cut_edge),
        tuple(map(str, ports)),
    )


def seed_poles():
    # In Fig. 1, the two connector pairs of M are (e1,e2) and (e3,e4).
    m = petersen_fragment({0, 1, 2}, None, (4, 5, 3, 7, 6))
    n = petersen_fragment({0}, (2, 3), (2, 3, 1, 5, 4))
    m_in_z, n_in_z = m.prefixed('M.'), n.prefixed('N.')
    e1, e2, e3, e4, e5 = m_in_z.ports
    f1, f2, f3, f4, f5 = n_in_z.ports
    z = Pole(
        m_in_z.edges + n_in_z.edges + (edge(e3, f1), edge(e4, f2), edge(e5, 'j'), edge(f5, 'j')),
        (e1, e2, f3, f4, 'j'),
    )

    # Fig. 3. The prime on the right-hand copy is represented by the R prefix.
    left, middle, right = z.prefixed('L.'), m.prefixed('C.'), z.prefixed('R.')
    l1, l2, l3, l4, l5 = left.ports
    r1, r2, r3, r4, r5 = right.ports
    e1, e2, e3, e4, e5 = middle.ports
    y1 = Pole(
        left.edges + middle.edges + right.edges
        + (edge(l3, e2), edge(l4, e1), edge(e4, r3), edge(e3, r4), edge(l5, r5)),
        (l1, l2, r1, r2, e5),
    )
    return z, y1


def boundary_types():
    one_port = tuple(1 << port for port in range(5))
    three_ports = tuple(31 ^ a ^ b for a, b in combinations(one_port, 2))
    types = [one_port + (31,)]
    for a, b in combinations_with_replacement(three_ports, 2):
        singles = [port for port in one_port for _ in range(2 - bool(a & port) - bool(b & port))]
        types.append(tuple(sorted((a, b, *singles))))
    assert len(types) == len(set(types)) == 56
    return tuple(types)


def port_labels(rows):
    return tuple(sum(1 << color for color in COLORS if rows[color] & (1 << port)) for port in range(5))


def color_rows(labels):
    return tuple(sum(1 << port for port, pair in enumerate(labels) if pair & (1 << color)) for color in COLORS)


def verify_labels(pole, internal, boundary):
    assert len(pole.edges) == len(set(pole.edges))
    assert set(internal) == set(pole.edges)
    assert len(pole.ports) == len(boundary)
    incident = {}
    for (u, v), pair in internal.items():
        assert u != v
        incident.setdefault(u, []).append(pair)
        incident.setdefault(v, []).append(pair)
    for vertex, pair in zip(pole.ports, boundary, strict=True):
        incident[vertex].append(pair)
    for pairs in incident.values():
        assert len(pairs) == 3 and all(pair in PAIR_SET for pair in pairs)
        assert pairs[0] | pairs[1] | pairs[2] == ALL_COLORS
    return len(incident)


def base_witnesses(pole):
    vertices = sorted({v for e in pole.edges for v in e})
    position = {v: i for i, v in enumerate(vertices)}
    neighbors = [[] for _ in vertices]
    for i, (u, v) in enumerate(pole.edges):
        a, b = position[u], position[v]
        neighbors[a].append((b, 1 << i))
        neighbors[b].append((a, 1 << i))

    @cache
    def perfect_matchings(remaining):
        if not remaining:
            return (0,)
        available = [i for i in range(len(vertices)) if remaining & (1 << i)]
        first = min(available, key=lambda i: sum(bool(remaining & (1 << j)) for j, _ in neighbors[i]))
        remaining ^= 1 << first
        return tuple(
            selected | rest
            for j, selected in neighbors[first] if remaining & (1 << j)
            for rest in perfect_matchings(remaining ^ (1 << j))
        )

    all_vertices = (1 << len(vertices)) - 1
    by_row = {
        mask: perfect_matchings(all_vertices ^ sum(1 << position[v] for i, v in enumerate(pole.ports)
                                                   if mask & (1 << i)))
        for mask in range(32) if mask.bit_count() % 2
    }
    all_edges = (1 << len(pole.edges)) - 1

    def assign(groups, once=0, twice=0):
        if not groups:
            return {} if twice == all_edges else None

        eligible = []
        available_once = available_twice = 0
        for color, options in groups:
            disjoint = [matching for matching in options if not matching & twice]
            if not disjoint:
                return None
            union = 0
            for matching in disjoint:
                union |= matching
            available_twice |= available_once & union
            available_once |= union
            eligible.append((color, disjoint))
        if (all_edges ^ twice) & ~available_once or (all_edges ^ once) & ~available_twice:
            return None

        i = min(range(len(eligible)), key=lambda j: len(eligible[j][1]))
        color, options = eligible[i]
        rest = eligible[:i] + eligible[i + 1:]
        for matching in options:
            solution = assign(rest, once | matching, twice | (once & matching))
            if solution is not None:
                return {**solution, color: matching}
        return None

    covers = {}
    for rows in boundary_types():
        witness = assign([(color, by_row[row]) for color, row in enumerate(rows)])
        assert witness is not None, rows
        labels = {
            e: sum(1 << color for color in COLORS if witness[color] & (1 << i))
            for i, e in enumerate(pole.edges)
        }
        assert verify_labels(pole, labels, port_labels(rows)) == len(vertices)
        covers[rows] = labels
    return covers, max(map(len, by_row.values()))


def permuted_cover(pole, witnesses, requested):
    rows = color_rows(requested)
    permutation = sorted(COLORS, key=rows.__getitem__)
    canonical = tuple(rows[i] for i in permutation)
    labels = {
        e: sum(1 << permutation[i] for i in COLORS if pair & (1 << i))
        for e, pair in witnesses[canonical].items()
    }
    verify_labels(pole, labels, requested)
    return labels


def remaining_pair(p, q):
    assert p in PAIR_SET and q in PAIR_SET and not p & q
    return ALL_COLORS ^ p ^ q


def transition(outer):
    alpha, beta, gamma, delta, epsilon = outer
    left_rhs = ALL_COLORS ^ alpha ^ beta
    right_rhs = ALL_COLORS ^ gamma ^ delta

    # Left free ports are a,b,f. Right free ports are c,d,g.
    d = next(p for p in PAIRS if not p & epsilon and p != (gamma ^ delta))
    c, g = next((p, q) for p, q in product(PAIRS, repeat=2) if p ^ q == right_rhs ^ d)
    f = next(p for p in PAIRS if not p & g and (left_rhs ^ p).bit_count() <= 4)
    a, b = next((p, q) for p, q in product(PAIRS, repeat=2) if p ^ q == left_rhs ^ f)

    # A,C are the top junctions. B,D,E are on the bottom chain. F is the
    # junction joining both z5 ports to the old epsilon.
    de = remaining_pair(d, epsilon)
    ac = next(p for p in PAIRS if not p & (a | c))
    bd = next(p for p in PAIRS if not p & (b | de))

    inner = (remaining_pair(b, bd), remaining_pair(bd, de), remaining_pair(a, ac),
             remaining_pair(c, ac), remaining_pair(f, g))
    left = (alpha, beta, a, b, f)
    right = (gamma, delta, c, d, g)
    universal = set(boundary_types())
    for row in (inner, left, right):
        assert tuple(sorted(color_rows(row))) in universal
    return inner, left, right, (ac, bd, de)


def extend(level, old, old_labels, outer, step, z, z_witnesses):
    inner, left, right, (ac, bd, de) = step
    left_pole, right_pole = z.prefixed(f'{level}.L.'), z.prefixed(f'{level}.R.')
    left_labels = permuted_cover(z, z_witnesses, left)
    right_labels = permuted_cover(z, z_witnesses, right)
    labels = dict(old_labels)
    for part, values in ((left_pole, left_labels), (right_pole, right_labels)):
        labels.update((new, values[original]) for new, original in zip(part.edges, z.edges, strict=True))

    A, B, C, D, E, F = (f'{level}.{j}' for j in 'ABCDEF')
    alpha, beta, gamma, delta, eps = old.ports
    l1, l2, l3, l4, l5 = left_pole.ports
    r1, r2, r3, r4, r5 = right_pole.ports
    connectors = (
        (A, l3, left[2]), (A, gamma, inner[2]), (B, l4, left[3]), (B, alpha, inner[0]),
        (C, r3, right[2]), (C, delta, inner[3]), (D, beta, inner[1]), (E, r4, right[3]),
        (F, l5, left[4]), (F, r5, right[4]), (F, eps, inner[4]),
        (A, C, ac), (B, D, bd), (D, E, de),
    )
    labels.update((edge(u, v), pair) for u, v, pair in connectors)
    pole = Pole(tuple(labels), (l1, l2, r1, r2, E))
    assert verify_labels(pole, labels, outer) == 40 * level + 1
    return pole, labels


def closed_graph(n, z, y1, z_witnesses, y1_witnesses):
    outer = (3, 3, 3, 12, 48)
    plan = []
    requested = outer
    for level in range(n, 1, -1):
        step = transition(requested)
        plan.append((level, requested, step))
        requested = step[0]

    pole = y1
    labels = permuted_cover(pole, y1_witnesses, requested)
    for level, requested, step in reversed(plan):
        pole, labels = extend(level, pole, labels, requested, step, z, z_witnesses)

    # Fig. 6. Alpha and gamma join to make pi, while the other ports meet x.
    alpha, beta, gamma, delta, epsilon = pole.ports
    labels.update({edge(alpha, gamma): 3, edge(beta, 'x'): 3, edge(delta, 'x'): 12, edge(epsilon, 'x'): 48})
    closed = Pole(tuple(labels), ())
    assert verify_labels(closed, labels, ()) == 40 * n + 2

    counts = Counter()
    matches = []
    for color in COLORS:
        matching = [e for e, pair in labels.items() if pair & (1 << color)]
        counts.update(matching)
        assert len({v for e in matching for v in e}) == 2 * len(matching) == 40 * n + 2
        matches.append(matching)
    assert set(counts) == set(labels) and set(counts.values()) == {2}
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, default=4, help='replay full covers for H_1 through H_n')
    parser.add_argument('--emit', action='store_true', help='include the full base and closed-graph witnesses as JSON')
    args = parser.parse_args()
    if args.n < 1:
        parser.error('--n requires a positive integer')

    z, y1 = seed_poles()
    z_witnesses, z_count = base_witnesses(z)
    y1_witnesses, y1_count = base_witnesses(y1)
    for rows in boundary_types():
        transition(port_labels(rows))
    result = {
        'Z': {'profiles': len(z_witnesses), 'largest_single_color_matching_count': z_count},
        'Y1': {'profiles': len(y1_witnesses), 'largest_single_color_matching_count': y1_count},
        'transition_profiles_verified': len(boundary_types()),
        'closed_graphs': {},
    }
    for n in range(1, args.n + 1):
        cover = closed_graph(n, z, y1, z_witnesses, y1_witnesses)
        result['closed_graphs'][n] = cover if args.emit else {'vertices': 40 * n + 2, 'matching_sizes': list(map(len, cover))}
    if args.emit:
        for name, pole, witnesses in [('Z', z, z_witnesses), ('Y1', y1, y1_witnesses)]:
            result[name]['ports'] = pole.ports
            result[name]['edges'] = pole.edges
            result[name]['covers'] = [
                {'rows': rows, 'edge_labels': [labels[e] for e in pole.edges]}
                for rows, labels in witnesses.items()
            ]
    print(json.dumps(result, indent=None if args.emit else 2))


if __name__ == '__main__':
    main()
