# Replaying the thirteen five-cut profile cases

Proposition 4.4 of Máčajová, Mazzuoccolo and Tabarelli restricts the exact profiles of a cyclic five-edge cut in a minimum Berge–Fulkerson counterexample. Twelve of the cases have an actual pentagon on one side. The thirteenth has two other profiles. These are necessary conditions for a minimum counterexample. The enumeration gives abstract profiles and does not require each to be realized by a pole. [Primary paper](https://doi.org/10.26493/1855-3974.3409.c13)

## Correcting the port labels in case XIII

Use the paper's notation $(ij)(kl)$ for the type whose two colors using three ports omit the pairs $ij$ and $kl$. A repeated pair is a loop. The published Appendix includes the all-five type in the right profile of case XIII. From it, switch the all-five color with the singleton color at port 2. Their open chain starting at port 1 ends at 3, 4, or 5, since the ports where just one of these colors occurs are $\{1,3,4,5\}$. The resulting boundary type is respectively $(13)(45)$, $(14)(35)$, or $(15)(34)$. The printed right profile omits all three. It therefore cannot be a five-pole profile, regardless of the order of the ports.

The replay recovers the corrected left profile as the two looped cliques on the labels

$$
\{12,15,23,34,45\},\qquad \{13,14,24,25,35\}.
$$

These label sets are complementary pentagons in $K_5$. The right profile is the 25 cross pairs plus the all-five type. Thus Figure 7 interchanges labels $25$ and $45$ between the two groups. In the Appendix, exchange those two labels in the right profile and replace $45$ by $25$ in the first block of the left profile. The second left block already matches the corrected labels. In the repository's bit order, the corrected pair is `b4abccc8f986b9` and `4b543337067946`, with 30 and 26 types respectively.

## Exact replay

The verifier enumerates all 56 single boundary types. For each type, it requires each choice of two colors to admit a chain switch on some paired endpoints. For two disjoint color pairs the profile must contain the two chosen single switches and their simultaneous switch. A color pair has at most four exclusive boundary endpoints. When it has four, the two chains of a pairing give the same type after switching and renaming those two colors. These conditions hold for every actual profile. The verifier also requires each side to meet and omit some type in every orientation of each of the two acyclic completions from Figure 4, as in the paper's minimum-counterexample argument.

One completion has a three-vertex path, whose heavy colors omit one port at each end. Its types form the looped clique on $14,15,24,25$ in the paper's ordering. The other has a three-stub vertex and a bare edge connecting ports 4 and 5. The two colors on that edge are the heavy colors, with omitted pairs among $12,13,23$. Both replacements preserve bridgelessness. In a minimum cyclically 5-edge-connected counterexample the poles are connected and have distinct terminals. An internal bridge cannot separate a tree of order $n$, since its boundary would need $n+2$ edges and has at most $n$ terminal edges plus the bridge. If both sides were cyclic each would need at least four terminals, also impossible. Gluing either cap to the remaining connected bridgeless pole creates only edges on cycles, since every branch of a cap reaches a terminal on the retained pole. The resulting graph is smaller and has a cover by minimality. Each original profile therefore meets each cap profile. Disjointness forces it to omit a type from that cap as well.

There are 430 distinct switch rules and 25 distinct completion masks. The two profile formulas plus 56 disjointness clauses give 1,716 ordered disjoint pairs. Under simultaneous five-port relabeling and exchange of the two sides they form 13 orbits. Twelve coincide with the published cases I–XII. The other orbit is the corrected case XIII above. This is an independent necessary-condition enumeration and does not use the paper’s intermediate count of individual profiles.

The archived pair list records the 1,716 projections. The verifier checks each from the switch and completion rules and regenerates one blocking clause per pair. DRAT-trim checks that the formula with all blockers is unsatisfiable. [Proof check](certificates/bf-five-profile-exhaustion.verified.txt)

```sh
python replay_five_targets.py --verify certificates/bf-five-profile-exhaustion
drat-trim certificates/bf-five-profile-exhaustion.cnf certificates/bf-five-profile-exhaustion.drat
```

The search in `target_five_poles.py` scores an actual profile by the number of boundary types that must be inserted or deleted to attain a classified profile under some port ordering. It excludes the pentagon itself as a search target. Any complete witness is checked for bridges and smaller cyclic cuts before running the full graph SAT verifier.
