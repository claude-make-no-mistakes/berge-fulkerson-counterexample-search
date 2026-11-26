"""Replay the five-cut boundary-profile enumeration in §4.3 of DOI 10.26493/1855-3974.3409.c13.

Run with the counterexample repository's NetworkX and python-sat dependencies installed.
The count concerns boundary type sets satisfying the paper's necessary conditions.
"""

import argparse
from itertools import combinations, combinations_with_replacement, product
from pathlib import Path

from pysat.formula import CNF
from pysat.solvers import Cadical195, Glucose4

from five_cut import TYPES, active_bits
from five_targets import COMPLEMENTARY_PAIR, PENTAGON, PENTAGON_PARTNERS, permutation_tables


TYPE_VARIABLE = {shape: index for index, shape in enumerate(TYPES, start=1)}
COLOR_PAIRS = tuple(combinations(range(6), 2))
PORT_MAPS = permutation_tables()
FULL = (1 << len(TYPES)) - 1


def omitted_pair_type(first, second):
    """Convert the paper's two omitted port pairs to a sorted color support tuple."""
    heavy = tuple(31 ^ sum(1 << (int(port) - 1) for port in pair) for pair in (first, second))
    light = [
        1 << port
        for port in range(5)
        for _ in range(2 - sum(bool(mask & (1 << port)) for mask in heavy))
    ]
    return tuple(sorted((*heavy, *light)))


def clique_profile(pair_labels):
    return sum(
        1 << (TYPE_VARIABLE[omitted_pair_type(first, second)] - 1)
        for first, second in combinations_with_replacement(pair_labels, 2)
    )


def relabel_profile(profile, port_map):
    return sum(port_map[index] for index in active_bits(profile))


def canonical_pair(left, right):
    return min(
        tuple(sorted((relabel_profile(left, port_map), relabel_profile(right, port_map))))
        for port_map in PORT_MAPS
    )


def endpoint_choices(shape, color_pair):
    first, second = color_pair
    ports = [1 << port for port in active_bits(shape[first] ^ shape[second])]
    if not ports:
        return ()
    # With four endpoints the other chain swaps the complementary two. Switching
    # that chain produces the same type up to exchanging the two color names.
    return tuple(ports[0] | other for other in ports[1:])


def switch_type(shape, *changes):
    supports = list(shape)
    for (first, second), endpoints in changes:
        supports[first] ^= endpoints
        supports[second] ^= endpoints
    return TYPE_VARIABLE[tuple(sorted(supports))]


def kempe_rules():
    """Generate requirements α implies at least one option is fully present."""
    rules = set()
    for shape, alpha in TYPE_VARIABLE.items():
        endpoints = {pair: endpoint_choices(shape, pair) for pair in COLOR_PAIRS}
        switchable = tuple(pair for pair, choices in endpoints.items() if choices)
        for pair in switchable:
            options = [(switch_type(shape, (pair, ends)),) for ends in endpoints[pair]]
            record_rule(rules, alpha, options)
        for first, second in combinations(switchable, 2):
            if set(first).intersection(second):
                continue
            options = []
            for first_ends, second_ends in product(endpoints[first], endpoints[second]):
                switch_first = (first, first_ends)
                switch_second = (second, second_ends)
                options.append((
                    switch_type(shape, switch_first),
                    switch_type(shape, switch_second),
                    switch_type(shape, switch_first, switch_second),
                ))
            record_rule(rules, alpha, options)
    return sorted(rules)


def record_rule(rules, alpha, options):
    options = {frozenset(option) - {alpha} for option in options}
    if frozenset() in options:
        return
    minimal = (tuple(sorted(option)) for option in options if not any(other < option for other in options))
    rules.add((alpha, tuple(sorted(minimal))))


def acyclic_caps():
    caps = set()
    for labels in (("12", "13", "23"), ("14", "15", "24", "25")):
        profile = clique_profile(labels)
        caps.update(relabel_profile(profile, port_map) for port_map in PORT_MAPS)
    return tuple(sorted(caps))


def profile_formula():
    rules = kempe_rules()
    clauses = []
    next_variable = len(TYPES) + 1
    auxiliaries = {}
    for alpha, choices in rules:
        required_choice = [-alpha]
        for option in choices:
            if len(option) == 1:
                required_choice.extend(option)
                continue
            auxiliary = auxiliaries.get(option)
            if auxiliary is None:
                auxiliary = next_variable
                next_variable += 1
                auxiliaries[option] = auxiliary
                clauses.extend([-auxiliary, variable] for variable in option)
            required_choice.append(auxiliary)
        clauses.append(required_choice)

    # Figure 4's two acyclic caps. Each orientation must meet both the
    # profile and its complement in a smallest counterexample.
    caps = acyclic_caps()
    for cap in caps:
        positive = [index + 1 for index in active_bits(cap)]
        clauses.extend((positive, [-variable for variable in positive]))
    return next_variable - 1, clauses, len(rules), len(caps)


def pair_formula():
    block_size, clauses, rule_count, cap_count = profile_formula()
    pair_clauses = clauses + [
        [literal + block_size if literal > 0 else literal - block_size for literal in clause]
        for clause in clauses
    ]
    pair_clauses.extend([-index, -(index + block_size)] for index in range(1, len(TYPES) + 1))
    return block_size, pair_clauses, rule_count, cap_count


def block_pair(left, right, block_size):
    return [-(base + i + 1) if mask >> i & 1 else base + i + 1
            for base, mask in ((0, left), (block_size, right)) for i in range(len(TYPES))]


def enumerate_disjoint_pairs(export=None):
    block_size, pair_clauses, rule_count, cap_count = pair_formula()
    profiles = tuple(range(1, len(TYPES) + 1))
    second_profiles = tuple(variable + block_size for variable in profiles)
    orbits = set()
    ordered_count = 0
    blockers = []
    ordered_pairs = []
    with Cadical195(bootstrap_with=pair_clauses) as solver:
        while solver.solve():
            positive = {variable for variable in solver.get_model() if variable > 0}
            left, right = (
                sum(1 << index for index, variable in enumerate(side) if variable in positive)
                for side in (profiles, second_profiles)
            )
            assert not left & right
            orbits.add(canonical_pair(left, right))
            ordered_count += 1
            blocker = block_pair(left, right, block_size)
            solver.add_clause(blocker)
            if export is not None:
                blockers.append(blocker)
                ordered_pairs.append((left, right))
    if export is not None:
        exhausted = CNF(from_clauses=[*pair_clauses, *blockers])
        with Glucose4(bootstrap_with=exhausted.clauses, with_proof=True) as solver:
            assert not solver.solve()
            proof = solver.get_proof()
        exhausted.to_file(str(export.with_suffix(".cnf")))
        export.with_suffix(".drat").write_text("\n".join(proof) + "\n", encoding="ascii")
        export.with_suffix(".pairs").write_text(
            "".join(f"{a:014x} {b:014x}\n" for a, b in ordered_pairs), encoding="ascii"
        )
    return orbits, ordered_count, rule_count, cap_count


def verify_archive(prefix):
    block_size, clauses, rule_count, cap_count = pair_formula()
    caps = acyclic_caps()
    rules = [(1 << (alpha - 1), tuple(sum(1 << (i - 1) for i in option) for option in choices))
             for alpha, choices in kempe_rules()]
    pairs = [tuple(int(mask, 16) for mask in row.split())
             for row in prefix.with_suffix(".pairs").read_text(encoding="ascii").splitlines()]
    assert len(pairs) == len(set(pairs)) == 1716
    for left, right in pairs:
        assert not left & right
        for side in (left, right):
            assert 0 < side <= FULL
            assert all(side & cap and ~side & cap for cap in caps)
            assert all(not side & bit or any(side & choice == choice for choice in choices)
                       for bit, choices in rules)
        clauses.append(block_pair(left, right, block_size))
    assert CNF(from_file=str(prefix.with_suffix(".cnf"))).clauses == clauses
    return {canonical_pair(*pair) for pair in pairs}, len(pairs), rule_count, cap_count


def main(export=None, verify=None):
    found, ordered_count, rule_count, cap_count = (
        verify_archive(verify) if verify is not None else enumerate_disjoint_pairs(export)
    )
    expected_pentagon_cases = {canonical_pair(profile, PENTAGON) for profile in PENTAGON_PARTNERS}
    assert len(expected_pentagon_cases) == 12 and expected_pentagon_cases <= found

    # In XIII, the looped cliques use the edges of complementary pentagons.
    # The printed Figure 7 swaps 25 and 45, and the Appendix repeats one label.
    left = clique_profile(("12", "15", "23", "34", "45")) | clique_profile(("13", "14", "24", "25", "35"))
    right = FULL ^ left
    assert (left, right) == COMPLEMENTARY_PAIR
    assert found - expected_pentagon_cases == {canonical_pair(left, right)}
    assert ordered_count == 1716
    print(f"{rule_count} Kempe rules and {cap_count} acyclic cap orientations")
    print(f"{ordered_count} ordered disjoint pairs, {len(found)} orbits")
    print(f"Case XIII left  {left:014x} ({left.bit_count()} types)")
    print(f"Case XIII right {right:014x} ({right.bit_count()} types)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--export", type=Path, help="Write the exhausted CNF, its DRAT proof, and the blocked pairs")
    mode.add_argument("--verify", type=Path, help="Check the listed pairs and reconstruct the exhausted CNF")
    args = parser.parse_args()
    main(args.export, args.verify)
