"""Find a cut of size at most four with a cycle on each side."""

import networkx as nx
from pysat.card import CardEnc
from pysat.formula import IDPool
from pysat.solvers import Glucose4


def small_cyclic_cut(graph):
    if len(graph) < 6:
        return None
    if graph.is_multigraph() or graph.is_directed() or nx.number_of_selfloops(graph) or any(d != 3 for _, d in graph.degree()):
        raise ValueError("Expected a simple cubic graph")

    side = {vertex: i for i, vertex in enumerate(graph, 1)}
    pool = IDPool(start_from=len(graph) + 1)
    edges = []
    clauses = [[1]]
    for u, v in graph.edges():
        a, b = side[u], side[v]
        crossing = pool.id()
        edges.append(crossing)
        clauses.extend([[-crossing, a, b], [-crossing, -a, -b], [crossing, -a, b], [crossing, a, -b]])
    for sign in (1, -1):
        # A forest on s>=3 vertices of a cubic graph has at least s+2 cut edges.
        clauses.extend(CardEnc.atleast([sign * x for x in side.values()], 3, vpool=pool).clauses)
    clauses.extend(CardEnc.atmost(edges, 4, vpool=pool).clauses)
    with Glucose4(bootstrap_with=clauses) as solver:
        if not solver.solve():
            return None
        true = set(solver.get_model())
    inside = {v for v in graph if side[v] in true}
    assert len(list(nx.edge_boundary(graph, inside))) <= 4
    assert not nx.is_forest(graph.subgraph(inside))
    assert not nx.is_forest(graph.subgraph(set(graph) - inside))
    return inside
