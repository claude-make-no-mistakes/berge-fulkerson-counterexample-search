# Berge–Fulkerson counterexample search

The Berge–Fulkerson conjecture asks whether every bridgeless cubic graph has six perfect matchings that cover each edge twice. This repository records verified covers and searches for incompatible boundary behaviors at cuts. The searches so far have produced no counterexample. [Conjecture and partial results](https://onlinelibrary.wiley.com/doi/full/10.1002/jgt.70097)

At a cut with (r) edges, represent each color by the set of ports it meets. Each color's port count has the same parity as (r), and each port belongs to two colors. Sorting the six sets removes the names of the colors. Two fragment colorings combine into a full cover whenever their port types agree after matching ports. [Five-cut analysis](https://doi.org/10.26493/1855-3974.3409.c13)

- Direct verification found covers for five published Petersen-coloring counterexamples and 200 sampled five-edge splices.
- The sampled fragment libraries contain a compatible boundary type for all 10,585,080 ordered five-port joinings and 121,680 ordered six-port joinings. These counts can include isomorphic graphs.
- The 1,000-fragment edge-switch pilot reduced the minimum number of compatible pentagon types from seven to four. A bridgeless splice with zero compatible types would refute the conjecture.

## Replay

Use Python 3.10, NetworkX 3.3, and `python-sat==1.9.dev25`. The original seed graph edge lists are available at the pinned source below. [Seed graph edge lists](https://github.com/fsantibanezleal/CAOS_RESEARCH/tree/7679b56e9cf19ed31c38e1db265aa6fbfd3e7aa2/problems/combinatorics/petersen-coloring/data)

```sh
python search.py controls.g6
python five_cut.py controls.g6 --path-limit 24
python six_cut.py controls.g6 --cap-per-graph 16
python narrow_poles.py controls.g6 --trials 1000
```
