# Berge–Fulkerson counterexample search

The Berge–Fulkerson conjecture asks whether every bridgeless cubic graph has six perfect matchings that cover each edge twice. This repository records verified covers and searches for incompatible boundary behaviors at cuts. The searches so far have produced no counterexample. [Conjecture and partial results](https://onlinelibrary.wiley.com/doi/full/10.1002/jgt.70097)

At a cut with $r$ edges, represent each color by the set of ports it meets. Each color's port count has the same parity as $r$, and each port belongs to two colors. Sorting the six sets removes the names of the colors. Two fragment colorings combine into a full cover whenever their port types agree after matching ports. [Five-cut analysis](https://doi.org/10.26493/1855-3974.3409.c13)

- Direct verification found covers for five published Petersen-coloring counterexamples and 200 sampled five-edge splices.
- The sampled fragment libraries contain a compatible boundary type for all 10,585,080 ordered five-port joinings and 121,680 ordered six-port joinings. These counts can include isomorphic graphs.
- The 1,000-fragment edge-switch pilot reduced the minimum number of compatible pentagon types from seven to four. A bridgeless splice with zero compatible types would refute the conjecture.
- A 2,500-fragment continuation reached one compatible type in a 68-vertex bridgeless splice. One matching uses all five cut edges and each of the other five uses one. The saved six matchings cover every edge twice. The checked DRAT certificate excludes every cover with no matching using all five cut edges.

The Petersen graph already has the same one-type behavior across a pentagon cut. The 68-vertex example also has a cyclic cut of size four, so the search now includes a filter for cyclic edge connectivity at least five, as required in a smallest counterexample. The 250-fragment pilot recovered the Petersen score among the controls and found no obstruction. [Small-cut reduction](https://doi.org/10.26493/1855-3974.3409.c13)

Every pentagon attachment admits the all-five boundary pattern on the pentagon side. The option `--avoid-all-ports` gives priority to fragments where that pattern is unavailable. A bipartite seed ensures this from the start. Its two sides have sizes differing by one and four ports lie on the larger side. A perfect matching on the fragment with all five port vertices removed would require equal remaining side sizes.

Among 2,200 switched fragments from the bipartite seed campaign, 655 excluded the all-five type. Every one of those fragments still had at least six compatible types for each pentagon attachment. A separate run against the narrow 63-vertex pole found 279 fragments without the all-five type among 1,000 inspected. For those 279 fragments every splice still had a common type.

With the cyclic cut filter and the bipartite restart both enabled, 194 of 600 inspected fragments lacked the all-five type. The minimum across their eligible pentagon attachments was six compatible types.

A further run moved the dangling edges to new vertices in 468 of 1,400 accepted mutations. Among all 1,400 fragments, 444 excluded the all-five type. The best eligible splice in that group still had six compatible types.

## Replay

Use Python 3.10, NetworkX 3.3, and `python-sat==1.9.dev25`. The original seed graph edge lists are available at the pinned source below. [Seed graph edge lists](https://github.com/fsantibanezleal/CAOS_RESEARCH/tree/7679b56e9cf19ed31c38e1db265aa6fbfd3e7aa2/problems/combinatorics/petersen-coloring/data)

```sh
python search.py controls.g6
python five_cut.py controls.g6 --path-limit 24
python six_cut.py controls.g6 --cap-per-graph 16
python narrow_poles.py controls.g6 --trials 1000
python narrow_poles.py controls.g6 --trials 2500 --seed 20261128 --restart narrow-poles.jsonl
python narrow_poles.py controls.g6 --trials 2200 --seed 20261201 --avoid-all-ports --bipartite-restart 32
python narrow_poles.py controls.g6 --trials 1000 --seed 20261202 --avoid-all-ports --bipartite-restart 32 --target-pole narrow-poles-valid.jsonl
python narrow_poles.py cyclic-controls.g6 --trials 250 --seed 20261203 --cyclic-five
python narrow_poles.py cyclic-controls.g6 --trials 600 --seed 20261204 --cyclic-five --avoid-all-ports --bipartite-restart 32
python narrow_poles.py cyclic-controls.g6 --trials 1400 --seed 20261206 --cyclic-five --avoid-all-ports --restart narrow-poles-cyclic-no-all.jsonl --move-terminals
python verify_single_type.py narrow-poles-valid.jsonl certificates/bf-single-type
drat-trim certificates/bf-single-type.cnf certificates/bf-single-type.drat
```
