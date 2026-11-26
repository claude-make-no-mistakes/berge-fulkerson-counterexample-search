"""Exact profile targets for Proposition 4.4 of Máčajová, Mazzuoccolo and Tabarelli."""

from functools import cache
from itertools import permutations

from five_cut import PORTS, TYPES, active_bits, relabel_type


PENTAGON = 0xA40A0C8030C609
PENTAGON_PARTNERS = (
    0x1085B10B8F3976, 0x1085F10BCF39F6, 0x08F5B12FCF39F6,
    0x08F5F12FCF3976, 0x08F5F12FCF39F6, 0x18F5B12FCF39F6,
    0x18F5F12FCF39F6, 0x4BF5B37F8F3976, 0x5BF5B37F8F3976,
    0x4BF5B37FCF39F6, 0x4BF5F37FCF39F6, 0x5BF5F37FCF39F6,
)
# Case XIII uses the corrected labeling recovered by the switch-rule replay.
COMPLEMENTARY_PAIR = (0xB4ABCCC8F986B9, 0x4B543337067946)
CASES = tuple((profile, PENTAGON) for profile in PENTAGON_PARTNERS) + (COMPLEMENTARY_PAIR,)
PORT_ORDERS = tuple(permutations(range(PORTS)))


@cache
def permutation_tables():
    positions = {shape: i for i, shape in enumerate(TYPES)}
    return tuple(tuple(1 << positions[relabel_type(shape, order)] for shape in TYPES) for order in PORT_ORDERS)


@cache
def orientations(profile):
    """Map each oriented profile to one permutation producing it."""
    bits = tuple(active_bits(profile))
    result = {}
    for order, table in zip(PORT_ORDERS, permutation_tables(), strict=True):
        result.setdefault(sum(table[i] for i in bits), order)
    return result


@cache
def targets():
    """Index aligned partner profiles, omitting the ordinary pentagon as a target."""
    result = {}
    for case, (left, right) in enumerate(CASES, 1):
        assert left & right == 0
        left_bits, right_bits = tuple(active_bits(left)), tuple(active_bits(right))
        for table in permutation_tables():
            a, b = sum(table[i] for i in left_bits), sum(table[i] for i in right_bits)
            result.setdefault(a, set()).add((case, b))
            if case == 13:
                result.setdefault(b, set()).add((case, a))
    return result


@cache
def nearest_target(profile):
    target = min(targets(), key=lambda mask: ((profile ^ mask).bit_count(), (profile & ~mask).bit_count(), mask))
    return (profile ^ target).bit_count(), (profile & ~target).bit_count(), target
