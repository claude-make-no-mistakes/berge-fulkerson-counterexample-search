# Berge–Fulkerson covers across a hexagon

Let $G$ be a cubic graph with an induced six-cycle, with positions $0,\ldots,5$ in cyclic order. Delete the cycle vertices to obtain the exterior $R$ with six corresponding semiedges. A Berge–Fulkerson coloring assigns a pair from six colors to each edge or semiedge, so the three pairs incident to each vertex partition the colors. In a closed graph, the edges of each color form a perfect matching and every edge belongs to two matchings.

**Theorem.** If the exterior is bipartite, then $G$ has a Berge–Fulkerson cover. With three ports in each bipartite class, $G$ is also 3-edge-colorable. Suppose instead that $G$ is a smallest counterexample, and that the six exterior terminal vertices are distinct. Then no partition of the exterior into two classes can have just one internal edge within its classes, or two such edges sharing a vertex. Two such edges in one class are also excluded when the other class contains exactly two ports at opposite positions around the hexagon.

## Boundary types and simultaneous switches

For each color, record the subset of ports using that color. The exterior has even order, since $3|V(R)|=2|E(R)|+6$. Each color uses an even number of ports by the same parity count. Sort the six subsets, forgetting color names. There are 701 types of six even subsets with each port appearing twice. Both sides can realize a common type precisely when their color names can be aligned and the colorings glued.

A single color on the hexagon uses a vertex-disjoint subset of its six internal edges, with the unmatched vertices taking their semiedges. Enumerate all such matchings and six-element multisets of them. Keep multisets giving every internal edge multiplicity two. At each vertex this also gives the semiedge multiplicity two. Thus the hexagon realizes exactly 92 types. [Exact replay](six_caps.py)

Fix an exterior coloring and two colors $a,b$. The edges and semiedges carrying exactly one of $a,b$ give paths and cycles, since every internal vertex has degree zero or two in this subgraph. The paths pair up the boundary ports carrying exactly one of those colors. Swapping $a,b$ along any subset of the paths gives another coloring. For three disjoint pairs of colors, the swaps can be chosen independently and performed together. Each pair's paths depend only on its two colors, even when paths for different pairs share an edge.

Let $A$ be any set containing all types of the exterior. For every type in $A$ and every partition of the six colors into pairs, enumerate the possible pairings of the exclusive ports within each color pair. The type survives only if at least one joint choice of the three port pairings has all simultaneous switch outcomes in $A$. Remove the failing types and repeat until stable. An actual type can never be removed because its realized coloring and actual path pairings always supply a successful choice. This procedure may keep abstract types that no pole realizes.

In the absence of a common type, start with all types allowed by the signed counts below, then remove the 92 hexagon types. In the unrestricted case the iteration reduces the remaining 609 types to 561. That set still meets the profile of each tested smaller cap, consisting of all labeled versions of three wires, two junctions, an edge and a wire, a four-vertex star or path, a triangle and junction, a double edge and two wires, and a square and wire. Thus these simultaneous switches and cap tests leave the unrestricted hexagon case unresolved. [Replay log](six-cap-closure.jsonl) · [Five-cut switch method](https://doi.org/10.26493/1855-3974.3409.c13)

## Signed port counts

Partition the exterior vertices into classes $+$ and $-$. Assume every internal edge crosses the partition except for $t$ edges within the $+$ class. Write $p$ for the number of ports at $+$ vertices and $d$ for the difference between the class sizes. Subtracting the degree sums gives

$$
3d=2p-6+2t.
$$

For a color $c$, let $m_c$ count its occurrences on the $t$ exceptional edges. The same count within that color gives

$$
\#(+\text{ ports using }c)-\#(-\text{ ports using }c)=d-2m_c.
$$

Across all six colors, the multiset of $m_c$ consists of six zeros for $t=0$ and two ones with four zeros for $t=1$. For two incident exceptions the labels are disjoint, giving four ones and two zeros. For two disjoint exceptions the possible multiplicities follow by letting their two-element labels overlap in zero, one, or two colors. Apply these tests to every one of the 701 types before the switch iteration.

For a bipartite exterior, $p$ is $0,3$, or $6$. Up to cyclic symmetry and exchange of the two classes, the $+$ positions have representatives $\varnothing$, $\{0,1,2\}$, $\{0,1,3\}$, and $\{0,2,4\}$. The stable set avoiding all hexagon types is empty in every case. The exterior has at least one coloring. To see this, group same-class ports into triples and add a new vertex for each triple, on the opposite side from its ports. This gives a cubic bipartite graph, possibly with parallel edges. Hall's theorem supplies a perfect matching, and repeating gives a decomposition into three matchings. Doubling each color and restricting to the exterior gives the stated coloring. Its profile must therefore meet that of the hexagon, proving the first assertion.

When $p=3$, use the three colors without doubling them. A type is then a partition of the six ports into three even color supports, with the same number of $+$ and $-$ ports of each color. Up to color names there are 16 possible types for each of the three $+$ arrangements. Compute the hexagon types by assigning one color to each cycle edge, requiring consecutive edges to have different colors and giving the missing color to each semiedge. Use the same path-switch test with one color pair at a time. For the successive $+$ arrangements above with $p=3$, the sizes of the sets avoiding the hexagon decrease as $11,8,2,0$, then $10,3,0$, and then $5,0$. The exterior starts with a 3-edge-coloring from the bipartite completion, so it must have one that extends to the hexagon.

For one exceptional edge inside $+$, $p$ is $2$ or $5$. For two, $p$ is $1$ or $4$. The following table gives a wire completion whose profile is disjoint from the stable set of exterior types avoiding the hexagon. The three wires are edges pairing up exterior terminals, with matching labels at the two ports of a wire.

| Exceptional edges | Positive ports | Number of surviving types | Wire completion |
| --- | --- | ---: | --- |
| One | $0,1$ | 368 | $01,23,45$ |
| One | $0,2$ | 0 | $01,23,45$ |
| One | $0,3$ | 248 | $03,12,45$ |
| One | $0,1,2,3,4$ | 222 | $01,25,34$ |
| Two sharing a vertex | $0$ | 222 | $03,12,45$ |
| Two sharing a vertex | $0,1,2,3$ | 368 | $01,23,45$ |
| Two sharing a vertex | $0,1,2,4$ | 0 | $01,23,45$ |
| Two sharing a vertex | $0,1,3,4$ | 248 | $01,25,34$ |
| Two in one class | $0,1,3,4$ | 286 | $01,25,34$ |

The one-edge and incident-two-edge rows cover all arrangements by rotations and reflections. The last row includes all label overlaps for two defects, and the two negative positions are opposite. The replay enumerates each wire completion from the equality constraints on its labels. For each row, it verifies that an exterior profile avoiding the hexagon would miss the stated completion.

## The smaller completions are bridgeless

A smallest counterexample is cyclically $5$-edge-connected. With distinct exterior terminals, each vertex of $R$ has internal degree at least two, so each component contains a cycle. Two components would require at least five ports each because the complement of each includes the hexagon, which is impossible with only six ports. If an internal bridge splits $R$, each side has minimum degree two except possibly at the bridge endpoint, which retains degree at least one. Each side contains a cycle. Its cut in $G$ is the bridge plus its ports, so each side needs at least four ports. This is also impossible. Thus $R$ is connected and bridgeless. [Small-cut reduction](https://doi.org/10.26493/1855-3974.3409.c13)

Adding three wires between distinct terminals gives a smaller bridgeless cubic multigraph. Parallel edges introduced by the wires are harmless for minimality. In a bridgeless cubic component, a double edge has two distinct external neighbors, unless the component consists of a triple edge. If the two external neighbors coincided, that neighbor's third edge would be a bridge. Suppress the double edge and its two endpoints into a single edge between the external neighbors. Other edges retain their cycles, and the new edge lies on the cycle obtained from an old cycle through the two external edges. Any coloring lifts by assigning the replaced edge's pair to both external edges and splitting the other four colors between the two parallel edges. A triple edge itself admits a coloring by splitting all six colors into three pairs. Induction therefore extends simple-graph minimality to these smaller multigraphs.

The graph closed by the wire completion admits a coloring by minimality. Restricting it to $R$ realizes one of the wire completion's types. If $R$ had no common type with the hexagon, the iteration would put its entire profile in the stable set, contradicting the disjointness in the table. This proves the remaining assertions.

## Mutation search

The search reorders the ports, switches pairs of internal edges, and moves individual port vertices. Each scored splice is bridgeless and has no cycle-separating cut of size at most four. The exact SAT test asks which of the 92 hexagon types occur on the exterior. A zero triggers a second solve on the full cubic graph and exports an unsatisfiability proof for independent checking. The scan is over sampled mutations.

The first run used 44 seed fragments and 5,000 mutation attempts. It scored 3,121 splices. The best score was nine common types, attained on a 20-vertex splice. Direct enumeration of its exterior perfect matchings also gives nine, and its six-matchings certificate checks the full graph. The scored inputs can include isomorphic graphs. [Run log](hexagon-search.jsonl) · [Cover](certificates/hexagon-best-cover.json)

~~~sh
python six_caps.py
python search_hexagons.py cyclic-controls.g6 --trials 5000
python search_hexagons.py cyclic-controls.g6 --trials 5000 --min-order 38 --seed 20261215
~~~
