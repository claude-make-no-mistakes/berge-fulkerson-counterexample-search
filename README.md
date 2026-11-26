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

## Exact five-cut results

- An independent replay recovered 1,716 ordered disjoint profiles in 13 orbits under the five-cut necessary conditions. It corrects the exchanged port labels in published case XIII. DRAT-trim accepted the exhaustion certificate. [Paper](five-cut-profiles.pdf) · [Corrected profiles and replay](FIVE-CUT-TARGETS.md)
- Six ordinary matching checks determine the profile of a bipartite five-pole. The method agreed with the previous SAT implementation on 253 inputs. A side of a cyclic five-edge cut has all 21 bipartite types if the graph has no cyclic cut of size at most three. Separately, five terminals on one side of a one-edge defect give 36, 45, or 55 types under cyclic 5-edge connectivity. Both pole classes are excluded from cyclic five-cuts of a smallest counterexample. [Proof](BIPARTITE-FIVE-POLES.md)
- The exact-profile search evaluated 4,300 mutations across two runs. The two closest poles each realized the case II target plus five extra types. Their corresponding pentagon splices still admitted covers and had cyclic cuts of size four. [Search](target-five-poles.jsonl) · [Continuation](target-five-poles-resumed.jsonl)
- A third run evaluated 900 mutations and scored 868 poles including seeds under the requirement of a pentagon splice with no cyclic cut of size at most four. Its closest pole had all the types of a case VII target plus nine extra types, eight of which are shared with the aligned pentagon. [Run log](target-five-poles-cyclic.jsonl)
- Every Mattiolo–Negrini–Pagani snark $H_n$ has a Berge–Fulkerson cover, even though the family has unbounded flow resistance. Two checked base poles and a uniform extension through every layer prove the result for all $n$. [Paper](flow-resistance.pdf) · [Proof and replay](FLOW-RESISTANCE.md)

## Hexagon cuts

A hexagon with bipartite exterior always admits a Berge–Fulkerson cover. With three ports in each class, the graph is 3-edge-colorable. With distinct exterior terminals, a smallest counterexample cannot have an exterior made bipartite by deleting one edge or two incident edges. Two same-side defects are also excluded when the two ports in the opposite class lie opposite each other around the hexagon. An exact signed-count and Kempe-switch calculation verifies the exclusions. [Paper](hexagon-cut.pdf) · [Proof and scope](HEXAGON-CUT.md) · [Replay](six-cap-closure.jsonl)

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
python replay_five_targets.py --verify certificates/bf-five-profile-exhaustion
drat-trim certificates/bf-five-profile-exhaustion.cnf certificates/bf-five-profile-exhaustion.drat
python target_five_poles.py cyclic-controls.g6 --restart narrow-poles-valid.jsonl --restart narrow-poles-cyclic-no-all.jsonl --restart narrow-poles-terminal.jsonl --trials 800 --seed 20261209
python target_five_poles.py cyclic-controls.g6 --restart target-five-poles.jsonl --restart narrow-poles-valid.jsonl --restart narrow-poles-terminal.jsonl --trials 3500 --seed 20261210
python target_five_poles.py cyclic-controls.g6 --restart target-five-poles-resumed.jsonl --restart narrow-poles-terminal.jsonl --pentagon-cyclic-five --trials 900 --seed 20261211
python verify_flow_resistance.py --n 8
python six_caps.py
python search_hexagons.py cyclic-controls.g6 --trials 5000
python search_hexagons.py cyclic-controls.g6 --trials 5000 --min-order 38 --seed 20261215
```
