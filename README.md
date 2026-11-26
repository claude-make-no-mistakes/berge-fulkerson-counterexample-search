# Berge–Fulkerson counterexample search

The Berge–Fulkerson conjecture asks whether every bridgeless cubic graph admits six perfect matchings covering each edge twice. This repository contains verified covers, exact boundary-profile classifications and exclusion proofs across five- and six-edge cuts, a proof of the conjecture for the unbounded-flow-resistance snarks $H_n$ of Mattiolo–Negrini–Pagani, and search logs for incompatible boundary behaviors. No counterexample has been found. ([Conjecture and partial results](https://onlinelibrary.wiley.com/doi/full/10.1002/jgt.70097); [five-cut framework](https://doi.org/10.26493/1855-3974.3409.c13))

At a cut with $r$ edges, represent each of the six colors by the subset of ports it meets. Each color's port count has the same parity as $r$, and each port belongs to two colors. Sorting the six subsets forgets color names and yields a boundary type; two fragment colorings glue into a full cover whenever their boundary types agree under matching ports.

## Papers and exact results

### Exact five-cut profiles and near-bipartite five-poles
- **Five-cut classification replay and case XIII correction:** An independent SAT replay recovers all 1,716 ordered disjoint profile pairs in 13 orbits under the Kempe-switch (430 rules) and acyclic-completion (25 orientations) necessary conditions. Twelve orbits coincide with published cases I–XII; the thirteenth corrects an exchange of port labels $25$ and $45$ in Figure 7 and the Appendix of Máčajová, Mazzuoccolo, and Tabarelli. The exhaustion CNF and DRAT proof are verified by `drat-trim`. [Paper (PDF)](five-cut-profiles.pdf) · [LaTeX](five-cut-profiles.tex) · [Corrected profiles and replay](FIVE-CUT-TARGETS.md) · [DRAT verification](certificates/bf-five-profile-exhaustion.verified.txt)
- **Bipartite and one-edge-defect five-poles:** Six ordinary matching checks determine the exact boundary profile of any bipartite five-pole (matching the SAT implementation on all tested inputs). A bipartite side of a cyclic five-edge cut in a simple cubic graph with no cyclic cut of size at most three realizes all 21 bipartite types, and its gluings with pentagons or other bipartite five-poles are 3-edge-colorable. Separately, a five-pole with five terminals on the defect-free side of a single internal edge defect realizes 36, 45, or 55 types under cyclic 5-edge-connectivity and always shares at least six types with every pentagon orientation. Together with the five-cut classification, both pole classes are excluded from cyclic five-edge cuts of a smallest counterexample. [Proof](BIPARTITE-FIVE-POLES.md)

### Unbounded-flow-resistance snarks $H_n$
- Every Mattiolo–Negrini–Pagani snark $H_n$ ($n \ge 1$, order $40n+2$) admits a Berge–Fulkerson cover, even though the family is cyclically 5-edge-connected and has unbounded flow resistance. Two finite base checks ($Z$ on 17 vertices and $Y_1$ on 41 vertices, each realizing all 56 five-port boundary types) and an explicit uniform algebraic extension through the recursive layer prove the result for all $n \ge 1$. Full six-matching covers for $H_1,\dots,H_8$ (orders 42 through 322) are archived in [certificates/bf-flow-resistance.json](certificates/bf-flow-resistance.json). [Paper (PDF)](flow-resistance.pdf) · [LaTeX](flow-resistance.tex) · [Proof and replay](FLOW-RESISTANCE.md)

### Hexagon cuts
- A cubic graph with an induced hexagon and bipartite exterior always admits a Berge–Fulkerson cover; with three ports in each bipartite class, it is 3-edge-colorable. In a smallest counterexample with six distinct exterior terminals, no two-class partition of the exterior can have one internal defect edge, two incident internal defect edges, or two defect edges in one class when the opposite class has two opposite ports around the hexagon. The proof uses signed port-count invariants, simultaneous Kempe-switch closure across the 701 six-port boundary types (92 hexagon types), and bridgeless three-wire completions. [Paper (PDF)](hexagon-cut.pdf) · [LaTeX](hexagon-cut.tex) · [Proof and scope](HEXAGON-CUT.md) · [Exact closure log](six-cap-closure.jsonl)

## Search campaigns and logs

- **Direct covers:** SAT verification confirmed Berge–Fulkerson covers for five published Petersen-coloring counterexamples ([controls.jsonl](controls.jsonl)) and 200 sampled five-edge splices ([splices.jsonl](splices.jsonl)).
- **Sampled joinings:** Sampled fragment libraries admit a compatible boundary type for all 10,585,080 ordered five-port joinings ([five-cut.jsonl](five-cut.jsonl)) and all 121,680 ordered six-port joinings ([six-cut.jsonl](six-cut.jsonl)) (counts may include isomorphic graphs).
- **Pentagon-splice edge-switch search:** A 1,000-fragment pilot ([narrow-poles.jsonl](narrow-poles.jsonl)) reduced the minimum compatible pentagon types from 7 to 4. A 2,500-fragment continuation ([narrow-poles-valid.jsonl](narrow-poles-valid.jsonl)) reached a single compatible type (the all-five type) in a 68-vertex bridgeless splice; the six-matching cover is in [certificates/bf-single-type.cover.json](certificates/bf-single-type.cover.json) and a `drat-trim`-verified DRAT certificate ([certificates/bf-single-type.verified.txt](certificates/bf-single-type.verified.txt)) excludes every cover with no matching using all five cut edges.
- **Cyclic 5-edge-connectivity and avoiding the all-five type:** The 68-vertex splice has a cyclic 4-edge cut, and the Petersen graph already exhibits the same single-type behavior across a pentagon cut. A 250-fragment cyclically 5-edge-connected pilot ([narrow-poles-cyclic-five.jsonl](narrow-poles-cyclic-five.jsonl)) recovered the Petersen score. Because every pentagon admits the all-five type, `--avoid-all-ports` with a bipartite seed prioritizes fragments omitting it:
  - 2,200 fragments from the bipartite seed ([narrow-poles-bipartite.jsonl](narrow-poles-bipartite.jsonl)): 655 omitted the all-five type; every one kept at least six compatible types per pentagon attachment.
  - 1,000 fragments spliced against the narrow 63-vertex pole ([narrow-poles-double.jsonl](narrow-poles-double.jsonl)): 279 omitted the all-five type, all retaining a common type.
  - 600 fragments with both cyclic-5 filtering and bipartite restart ([narrow-poles-cyclic-no-all.jsonl](narrow-poles-cyclic-no-all.jsonl)): 194 omitted the all-five type, minimum six compatible pentagon types.
  - 1,400 fragments adding terminal moves ([narrow-poles-terminal.jsonl](narrow-poles-terminal.jsonl)): 468 accepted terminal moves and 444 fragments without the all-five type, minimum six compatible pentagon types.
- **Exact five-cut target search:** Across two runs totaling 4,300 mutations ([target-five-poles.jsonl](target-five-poles.jsonl), [target-five-poles-resumed.jsonl](target-five-poles-resumed.jsonl)), the two closest poles each realized the case II target plus 5 extra types (their pentagon splices admit covers and have cyclic 4-cuts). A third run of 900 mutations (868 scored poles under cyclic-5 pentagon splices, [target-five-poles-cyclic.jsonl](target-five-poles-cyclic.jsonl)) reached a case VII target plus 9 extra types (8 shared with the aligned pentagon).
- **Hexagon mutation search:** 5,000 mutation attempts from 44 seeds scored 3,121 cyclically 5-edge-connected splices ([hexagon-search.jsonl](hexagon-search.jsonl)), reaching a minimum of 9 common types on a 20-vertex splice ([certificates/hexagon-best-cover.json](certificates/hexagon-best-cover.json)).

## Replay

Use Python 3.10+ (tested on Python 3.12), NetworkX 3.3+, and `python-sat==1.9.dev25`, plus `drat-trim` for DRAT certificates. Note that `verify_flow_resistance.py` requires only the Python standard library. The original seed graph edge lists are available at [CAOS_RESEARCH](https://github.com/fsantibanezleal/CAOS_RESEARCH/tree/7679b56e9cf19ed31c38e1db265aa6fbfd3e7aa2/problems/combinatorics/petersen-coloring/data).

### Exact proofs and certificates

```sh
python3 replay_five_targets.py --verify certificates/bf-five-profile-exhaustion
drat-trim certificates/bf-five-profile-exhaustion.cnf certificates/bf-five-profile-exhaustion.drat
python3 verify_flow_resistance.py --n 8
python3 six_caps.py
python3 verify_single_type.py narrow-poles-valid.jsonl certificates/bf-single-type
drat-trim certificates/bf-single-type.cnf certificates/bf-single-type.drat
```

### Controls and search campaigns

```sh
python3 search.py controls.g6
python3 five_cut.py controls.g6 --path-limit 24
python3 six_cut.py controls.g6 --cap-per-graph 16
python3 narrow_poles.py controls.g6 --trials 1000
python3 narrow_poles.py controls.g6 --trials 2500 --seed 20261128 --restart narrow-poles.jsonl
python3 narrow_poles.py controls.g6 --trials 2200 --seed 20261201 --avoid-all-ports --bipartite-restart 32
python3 narrow_poles.py controls.g6 --trials 1000 --seed 20261202 --avoid-all-ports --bipartite-restart 32 --target-pole narrow-poles-valid.jsonl
python3 narrow_poles.py cyclic-controls.g6 --trials 250 --seed 20261203 --cyclic-five
python3 narrow_poles.py cyclic-controls.g6 --trials 600 --seed 20261204 --cyclic-five --avoid-all-ports --bipartite-restart 32
python3 narrow_poles.py cyclic-controls.g6 --trials 1400 --seed 20261206 --cyclic-five --avoid-all-ports --restart narrow-poles-cyclic-no-all.jsonl --move-terminals
python3 target_five_poles.py cyclic-controls.g6 --restart narrow-poles-valid.jsonl --restart narrow-poles-cyclic-no-all.jsonl --restart narrow-poles-terminal.jsonl --trials 800 --seed 20261209
python3 target_five_poles.py cyclic-controls.g6 --restart target-five-poles.jsonl --restart narrow-poles-valid.jsonl --restart narrow-poles-terminal.jsonl --trials 3500 --seed 20261210
python3 target_five_poles.py cyclic-controls.g6 --restart target-five-poles-resumed.jsonl --restart narrow-poles-terminal.jsonl --pentagon-cyclic-five --trials 900 --seed 20261211
python3 search_hexagons.py cyclic-controls.g6 --trials 5000
python3 search_hexagons.py cyclic-controls.g6 --trials 5000 --min-order 38 --seed 20261215
```
