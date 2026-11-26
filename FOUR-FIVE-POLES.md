# Four cyclic five-edge cuts in Berge–Fulkerson

**Theorem.** A smallest counterexample to the Berge–Fulkerson conjecture cannot have a partition into four vertex sets, each of which induces a subgraph containing a cycle and has exactly five edges leaving it.

A Berge–Fulkerson coloring gives each edge a two-element subset of six colors. At every cubic vertex the three subsets partition the colors, so each color supplies a perfect matching. The boundary profile of a pole is the set of realizable assignments to its semiedges up to renaming the six colors. Represent an assignment by its six color supports on the ports, sorted as integers.

## Reduction to one connection pattern

Suppose a smallest counterexample has the four parts $P_0,P_1,P_2,P_3$. It is cyclically 5-edge-connected by the small-cut reduction. Each part boundary is a cycle-separating five-edge cut. Its terminals on each side of the cut are distinct. If a vertex met at least two cut edges, moving it across the cut would shrink the cut and preserve a cycle on each side. The vertex originally has degree at most one on its own side, so it belongs to no cycle there. [Small-cut reduction](https://iris.univr.it/handle/11562/1030915)

Write $m_{ij}$ for the number of edges between parts $i$ and $j$. The four degree equations $\sum_{j\ne i}m_{ij}=5$ give $m_{01}=m_{23}$, $m_{02}=m_{13}$, and $m_{03}=m_{12}$. The boundary of $P_i\cup P_j$ is cycle-separating and has size $10-2m_{ij}$, so $m_{ij}\leq2$. The three multiplicities at a part sum to five. They are therefore 2, 2, and 1. Relabel the parts so the pairs of multiplicity two are $01,02,13,23$ and the pairs of multiplicity one are $03,12$.

In Proposition 4.4 of Máčajová, Mazzuoccolo and Tabarelli, cases I–XII require a side that is a literal pentagon. The complement of any one part includes the other three cyclic parts and hence cannot be a pentagon. Thus a part is either a pentagon, with its 16-type profile, or it has one of the two complementary profiles of case XIII, with 26 or 30 types. The replay uses the corrected case XIII labeling. There are 12 port orders of the pentagon profile and six of each other profile after duplicate sets are removed, giving 24 profile choices for a labeled part. [Proposition 4.4](https://doi.org/10.26493/1855-3974.3409.c13) · [Corrected classification](FIVE-CUT-TARGETS.md)

## Composing two profiles

Label the ports of $P_0$ and $P_1$ so ports 0 and 1 connect in order, and do the same for $P_2,P_3$. The six external ports of each half are the three remaining ports of its first part followed by those of its second part. Number them 0 through 5. In the left half the ports $0,1$ connect to $P_2$ and port 2 to $P_3$. Ports $3,4$ connect to $P_3$ and port 5 to $P_2$. In the right half choose the orders so right ports $0,\ldots,5$ connect to left ports $0,1,5,3,4,2$, respectively. Every possible local port labeling is already among the 24 profiles.

For a pair of five-port assignments, the two port labels on the join are ordered pairs of two-element sets. Up to color names, they are determined by whether the sets intersect in zero, one, or two colors. In each class choose a fixed ordered pair of sets. For each constituent profile, enumerate its types and all color permutations that send its joining labels to the fixed pair. Record every resulting assignment on the remaining three ports.

For each class take all pairs of the recorded three-port assignments. Their concatenations, with color names forgotten, give exactly the six-port profile of the combined pole. Every recorded pair comes from realizable assignments with equal labels on both joined edges. Conversely a coloring of the combined pole restricts to constituent colorings whose join labels agree and can be normalized by a common color permutation. The calculation only uses the boundary profiles.

Applying this composition to the 24 profile choices gives 576 entries per half, with 288 distinct sets. Apply the fixed port permutation to the right half and compare all $24^4=331{,}776$ choices. Every intersection contains at least 27 types. A common type glues the two colorings into a cover of the smallest counterexample, a contradiction. [Exact replay](four-five-poles.jsonl)

## Search of actual fragments

A separate run includes the ordinary pentagon and four previously logged five-poles. It constructs all 3,000 combinations of constituent pairs and two-edge joins, obtaining 628 distinct ordered six-port profiles. The smallest has 129 types. The scan checked 101,596,950 relative profile alignments, counting each distinct relabeling of the right profile once for each unordered pair of profiles. Every alignment shared at least 17 types. These are exact results for the fixed five-pole library. [Run log](composed-six-poles.jsonl)

### Replay

The analytic reduction is independent of the sampled library. The finite proof and the separate corpus search run as follows with the repository's NetworkX and python-sat versions.

~~~sh
python compose_six_poles.py --classified-four-cuts
python compose_six_poles.py narrow-poles-valid.jsonl narrow-poles-terminal.jsonl target-five-poles-resumed.jsonl target-five-poles-cyclic.jsonl
~~~
