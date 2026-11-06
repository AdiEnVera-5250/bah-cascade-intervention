# Model Specification

**Version:** 0.2.0
**Status:** normative
**Last updated:** 2026-11-06

This document is the scientific source of truth for the project. If the code and
this document disagree, this document prevails unless an ADR records an explicit
change. Working rules live in `AGENTS.md`.

## 1. Scope

This document specifies:

- the network growth model with two groups and symmetric homophily;
- the two-phase growth intervention;
- the threshold cascade model;
- the experimental design, parameter grids, and replication scheme;
- the definitions of the metrics and the analysis plan.

This document does not specify the implementation, the CSV layout, or the formal
statistical inference. The data contract lives in `docs/data-contracts.md`; formal
inference is deferred until the descriptive analysis is complete.

## 2. Notation

| Symbol | Meaning |
|---|---|
| `N1`, `N2`, `N` | Nodes at the end of phase 1, nodes added in phase 2, total nodes (`N = N1 + N2`) |
| `m` | Edges brought by each arriving node |
| `m0` | Number of nodes in the seed graph (`m0 = 2(m+1)`) |
| `p`, `p1`, `p2` | Probability that an arriving node belongs to group `A`, overall and per phase |
| `h`, `h1`, `h2` | Homophily weight, overall and per phase |
| `h_ij` | Pair weight between node `i` and an arriving node `j` |
| `k_i` | Degree of node `i` |
| `n_A`, `n_B` | Total number of nodes in groups `A` and `B` |
| `phi_i` | Threshold of node `i` |
| `Phi` | Grid of homogeneous thresholds used in the study |
| `S_N` | Cascade size: number of active nodes at steady state, including seeds |
| `S_A`, `S_B` | Number of active nodes in groups `A` and `B` at steady state |
| `t_s` | Number of synchronous steps until steady state |
| `G0` | Base graph produced by phase 1 |
| `G` | Control network: phase 2 under the null intervention `(h1, p1)` |
| `G'` | Intervened network: phase 2 under `(h2, p2)` |
| `R` | Number of independent base graphs per baseline |
| `H`, `P`, `M` | Grids of homophily, proportion, and arriving edges |
| `I` | Set of intervention pairs `((h1,p1),(h2,p2))`, defined separately for each `m` |
| `\bar{S}_N(G)` | Mean of `S_N` over all seeds of network `G` for a fixed threshold |
| `\tilde{S}_N(G)` | Median of `S_N` over all seeds of network `G` for a fixed threshold |
| `Delta S_N` | Paired difference of a network-level summary (mean and/or median) between an intervened network and its control |

Throughout the document, `A` is the group whose arrival probability is `p`, and
`B` is the complementary group.

## 3. Network model

### 3.1 Groups and parameters

The network is undirected and simple: no self-loops and no multiple edges. Every
node belongs to exactly one of two groups, `A` or `B`.

The parameter `p ∈ [0,1]` is the probability that an arriving node belongs to
group `A`. Each arrival is independent of previous arrivals, so the number of `A`
nodes after `n` arrivals is `Binomial(n, p)`. This is a model choice; exact group
quotas are not used (see decision D1).

The parameter `h ∈ [0,1]` is the homophily weight. It is not the realized
probability of same-group attachment. For an arriving node `j`, the pair weight is

$$
h_{ij} =
\begin{cases}
h & \text{if } g_i = g_j, \\
1 - h & \text{if } g_i \neq g_j.
\end{cases}
$$

The realized probability of attaching to a node of the same group follows from
the kernel in Section 3.4 and also depends on the current degrees.

### 3.2 Seed graph

The seed graph has `m0 = 2(m+1)` nodes, with exactly `m+1` nodes labeled `A` and
`m+1` nodes labeled `B`. Its topology depends only on the phase-1 homophily `h1`;
phase 2 does not modify the seed graph.

- **`h1 = 0`:** complete bipartite graph `K_{m+1,m+1}`, with the two sides equal to
  the two groups. There are no within-group edges. Every seed node has degree
  `m+1`.
- **`h1 = 1`:** two disjoint complete graphs `K_{m+1}`, each containing only nodes
  of one group. The two components are connected internally and disconnected from
  each other. Every seed node has degree `m`.
- **`0 < h1 < 1`:** complete graph `K_{2(m+1)}`. The group labels are a uniformly
  random permutation of `m+1` labels `A` and `m+1` labels `B`. Every seed node has
  degree `2m+1`.

For `h1 = 0`, which bipartition side receives label `A` is chosen uniformly at
random. For `h1 = 1`, which component receives label `A` is chosen uniformly at
random. For intermediate `h1`, the label assignment is a uniform random
permutation.

The three regimes have different seed edge counts. This is a deliberate design
choice that makes the extreme regimes exact; it is not an error and is recorded as
decision D2.

### 3.3 Arrival process

At each step, one node `j` arrives. Its group is drawn first, independently:

$$
g_j =
\begin{cases}
A & \text{with probability } p, \\
B & \text{with probability } 1-p.
\end{cases}
$$

The node then creates exactly `m` distinct edges to existing nodes. The targets are
sampled without replacement according to the kernel in Section 3.4. Self-loops are
impossible because `j` is not part of the existing node set when its neighbors are
chosen. Multiple edges are avoided by removing each chosen target from the
eligible set for the remaining draws.

The order of random draws is part of the reference implementation: first the group
of `j`, then the `m` target selections, then the update of the degree bag. This
order must be preserved for reproducibility.

### 3.4 Attachment kernel

For an arriving node `j`, the probability of choosing existing node `i` as the
next target is

$$
\Pi_i^{(j)} = \frac{h_{ij}\, k_i}{\sum_{l \in V} h_{lj}\, k_l}.
$$

The denominator runs over all existing nodes. Because every seed node has positive
degree and every arriving node brings `m ≥ 1` edges, the denominator is positive at
every step. When `h = 1`, cross-group weights are zero; when `h = 0`, within-group
weights are zero. Both cases remain well defined because each group has at least
`m+1` seed nodes.

The target draws are sequential and without replacement. After a target has been
chosen, it is excluded from the denominator for the remaining draws of the same
arriving node. This is the sequential version of the kernel, not `m` independent
draws from the same distribution.

### 3.5 Reference implementation: degree bag with rejection

The kernel is implemented by a degree bag and rejection sampling. This algorithm
is distributionally equivalent to direct sampling from `Pi_i`; it is recorded here
because it fixes the order of random draws and the handling of repeated targets.

**Data structure.** Maintain a bag `B` (a multiset of node identifiers) in which
every node `i` appears exactly `deg(i)` times. The bag therefore has size `2|E|`.
It is initialized from the seed graph and updated after every arrival.

**Selection.** For an arriving node `j` with group `g_j`:

```
used = empty set
chosen = empty list

while len(chosen) < m:
    i = B[rng.integers(0, len(B))]
    if i in used:
        continue
    if g_i == g_j:
        accept = h
    else:
        accept = 1 - h
    if rng.random() >= accept:
        continue
    used.add(i)
    chosen.append(i)

for i in chosen:
    add_edge(i, j)

add m copies of j to B
for i in chosen:
    add one copy of i to B
```

**Why it is equivalent.** A uniform draw from `B` selects node `i` with probability
`k_i / sum_l k_l`. Conditional on acceptance, the probability is proportional to
`h_{ij} k_i`, which is exactly `Pi_i^(j)`. Rejected draws do not change the
conditional distribution. The `used` set implements sampling without replacement
for the `m` targets.

**Removal is logical, not physical.** The chosen node is excluded through `used`;
its copies are not deleted from `B`. Deleting them would require restoring them
with the updated degree, which is error-prone. Logical removal is equivalent for
the duration of the `m` draws and keeps the bag equal to the degree multiset.

**Cost.** The expected number of draws per edge is the inverse of the acceptance
rate and is at most `max(1/h, 1/(1-h))` in the interior of the interval. At the
boundaries only one group is accepted; the expected number of draws is then the
ratio between the total degree mass and the preferred group's degree mass. Since
each group has at least `m+1` nodes at all times, the loop terminates with
probability one.

**Boundary cases.** At `h = 0`, same-group candidates are always rejected and only
cross-group candidates are accepted. At `h = 1`, cross-group candidates are always
rejected and only same-group candidates are accepted. At `h = 1`, the graph remains
disconnected into the two group components; at `h = 0`, the graph remains bipartite
with sides `A` and `B`, provided phase 2 also uses the extreme value.

### 3.6 Two-phase growth

Growth proceeds in two phases:

- **Phase 1.** The seed graph is grown with parameters `(h1, p1)` until the graph
  has `N1` nodes. The resulting graph is the base graph `G0`.
- **Phase 2.** The graph is grown with parameters `(h2, p2)` by adding `N2` nodes,
  until the total is `N = N1 + N2`.

The bag is carried from phase 1 to phase 2. Because the bag is a function of the
current graph, it can be rebuilt from `G0` before each phase-2 run.

An intervention changes `h`, `p`, or both:

- **behavioral:** `h2 != h1` and `p2 = p1`;
- **size:** `h2 = h1` and `p2 != p1`;
- **mixed:** `h2 != h1` and `p2 != p1`.

The **control** network is the null intervention `(h2, p2) = (h1, p1)`. It is
generated from the same `G0` with its own independent phase-2 randomness.

### 3.7 Invariants and edge cases

- The graph is undirected and simple.
- Every node has degree at least `m`. Seed nodes have degree at least `m` by the
  construction in Section 3.2; every arriving node brings `m` edges.
- No isolated nodes are created, because `m >= 1`.
- The number of `A` nodes is random. For `N1 = N2`, the expected final fraction of
  `A` nodes is `(p1 + p2) / 2`. The realized values `n_A` and `n_B` are recorded
  for every network.
- If `h1 = 0`, `G0` is bipartite with sides `A` and `B`. If `h2 = 0` as well, the
  final network is bipartite.
- If `h1 = 1`, `G0` is disconnected into the two group components. If `h2 = 1` as
  well, the final network is disconnected.
- If `h1 = 0` but `h2 > 0`, phase 2 can add within-group edges and the final
  network need not be bipartite. If `h1 = 1` but `h2 < 1`, phase 2 can add
  cross-group edges and the final network need not be disconnected.

## 4. Cascade model

### 4.1 Thresholds

In the general model, each node `i` has a threshold `phi_i ∈ [0,1]` drawn from a
distribution `f` with support on `[0,1]`. The main study uses a homogeneous
threshold: every node in a network has the same `phi ∈ Phi`. Heterogeneous
thresholds are left as a robustness check on a restricted subset of the design.

### 4.2 Update rule

Let `A(t)` be the set of active nodes at step `t`, and let

$$
k_i^{A}(t) = |N(i) \cap A(t)|
$$

be the number of active neighbors of node `i` at step `t`. A node becomes active
when

$$
k_i^{A}(t) \ge \lceil \phi_i\, k_i \rceil .
$$

Updates are synchronous: every node evaluates the rule against `A(t)`, and all
newly active nodes are added at once. The update is

$$
A(t+1) = A(t) \cup
\left\{ i \notin A(t) : k_i > 0 \ \text{and}\ k_i^{A}(t) \ge \lceil \phi_i k_i \rceil \right\}.
$$

A node that is active remains active.

### 4.3 Isolated nodes

If `k_i = 0`, the right-hand side of the threshold rule is `0`, so the rule would
activate the node at the first step even with no active neighbor. By convention,
nodes of degree zero remain inactive. Under the design in Section 3, no isolated
nodes are created, so this convention is a safety rule rather than an operative
case.

For `phi = 0` and `k_i > 0`, the same trivial activation occurs, because
`ceil(0) = 0`. The study grid starts at `phi = 0.10`, so this case is outside the
main design. If `phi = 0` is ever used, the model behaves as described and this
must be documented in the run metadata.

### 4.4 Seeds

At time zero, a seed set `S0` is activated and all other nodes are inactive. The
general model allows any non-empty `S0`. The main study uses a single seed,
`|S0| = 1`, and enumerates every node of the network as the seed. No seed sampling
is used in the main design.

### 4.5 Steady state and cascade metrics

Let `t_s` be the first step at which no new node activates:

$$
t_s = \min\{ t \ge 0 : A(t+1) = A(t) \}.
$$

If the seed activates no other node, `t_s = 0`. The cascade size is

$$
S_N = |A(t_s)|,
$$

and it includes the initial seed. The active counts by group are

$$
S_A = |A(t_s) \cap A|, \qquad S_B = |A(t_s) \cap B|,
$$

so `S_N = S_A + S_B`.

The relative cascade size is `S_N / N`.

### 4.6 Global cascades

A cascade is global when more than half of the network is active at steady state:

$$
S_N > N/2.
$$

The indicator is `1[S_N > N/2]`. The boundary `S_N = N/2` is not global.

When the network is disconnected, a cascade cannot leave the seed's component. In
particular, if `h1 = h2 = 1`, the components are the two groups, so a global
cascade is possible only from the group whose size exceeds `N/2`. If neither group
exceeds `N/2`, the probability of a global cascade is structurally zero for that
network. This is a property of the model, not a missing observation.

## 5. Experimental design

### 5.1 Factor grids

$$
H = \{0.0, 0.2, 0.5, 0.8, 1.0\},
$$

$$
P = \{0.2, 0.4, 0.5, 0.6, 0.8\},
$$

$$
M = \{1, 2, 4\},
$$

$$
\Phi = \{0.10, 0.15, 0.20, 0.25\}.
$$

The pairs of `H x P` are 25. The arriving-edge count `m ∈ M` is a crossed factor,
so a baseline is the triple `(h1, p1, m)` and there are `25 x 3 = 75` baselines.
For each baseline, the seed graph is determined by `h1` as in Section 3.2.

### 5.2 Intervention set

The full intervention set is

$$
I = \left\{ ((h1,p1),(h2,p2)) \in (H \times P)^2 : (h1,p1) \neq (h2,p2) \right\},
$$

with cardinality `25^2 - 25 = 600`. The set is defined per value of `m`; the same
600 pairs apply at each `m ∈ M`.

For a fixed baseline `(h1, p1, m)`, the 600 pairs reduce to 24 alternative targets
`(h2, p2) != (h1, p1)`. They split into:

- **behavioral:** `p2 = p1` and `h2 != h1`, `25 x 4 = 100` cells;
- **size:** `h2 = h1` and `p2 != p1`, `25 x 4 = 100` cells;
- **mixed:** `h2 != h1` and `p2 != p1`, `25 x 16 = 400` cells.

The main design uses the complete set, so every baseline is paired with all 24
interventions. The control `(h2, p2) = (h1, p1)` is not part of `I` and is
generated separately for every base graph.

### 5.3 Sizes and replication

- `N1 = 250`, `N2 = 250`, so `N = 500`.
- `m0 = 2(m+1)`, with `m+1` seed nodes per group.
- `R` independent base graphs per baseline. The pilot value is `R = 50`; the final
  value is fixed by a power analysis at the level of `G0`.

For the main design, the number of networks is

$$
75\,R\,(1 + 24) = 1875\,R,
$$

where `75` is the number of baselines `(h1, p1, m)`, `1` is the control, and `24`
are the alternative targets `(h2, p2) != (h1, p1)`. With `R = 50`, this is 93,750
networks. Each network is simulated with `N = 500` seeds and `|Phi| = 4`
thresholds, for 187.5 million cascades in total.

A reduced design that keeps only the four behavioral and four size interventions
has

$$
75\,R\,(1 + 8) = 675\,R,
$$

which is 33,750 networks and 67.5 million cascades at `R = 50`. It is available as
a cheaper option but is not the main design.

The full design is computationally demanding. At 187.5 million cascades, the
cascade engine must avoid one `networkx` object per cascade; a vectorized or
compiled implementation is required. The pilot value `R = 50` is provisional and
can be reduced if the measured throughput makes the full run impractical. The
final value of `R` comes from a power analysis at the level of `G0`.

### 5.4 Paired design

For each baseline `(h1, p1, m)` and each replicate `r`, generate a base graph
`G0^(r)`. From that same base graph, generate:

- the control `G^(r)` by continuing growth with `(h1, p1)` for `N2` nodes;
- every intervened network `G'^(r)_{h2,p2}` by continuing growth with `(h2, p2)`
  for `N2` nodes.

The paired difference at the network level is

$$
\Delta \bar{S}_N = \bar{S}_N(G') - \bar{S}_N(G),
$$

where

$$
\bar{S}_N(G) = \frac{1}{N} \sum_{s \in V(G)} S_N(G; s, \phi)
$$

is the mean cascade size over all seeds for a fixed threshold `phi`. The median
counterpart is

$$
\tilde{S}_N(G) = \operatorname{median}\{ S_N(G; s, \phi) : s \in V(G) \},
$$

and `Delta \tilde{S}_N = \tilde{S}_N(G') - \tilde{S}_N(G)`. The same definitions
apply to `t_s`, `S_A`, and `S_B`. The analysis reports differences of means and
differences of medians.

The unit of replication is `G0`, not the intervention cell. All intervened networks
derived from the same `G0` share phase 1 and the same control, so their paired
differences are correlated. The effective sample size for between-network effects
is `R`, not `R` times the number of intervention cells. The descriptive analysis
aggregates over `R`; formal inference must account for the dependence, for example
with a random intercept for `G0`, cluster-robust standard errors at the level of
`G0`, or aggregation to one summary per `(G0, h2, p2)` cell.

### 5.5 Randomness and seeding

Every stochastic process receives an explicit `numpy.random.Generator` derived
from a master seed through `numpy.random.SeedSequence`. The global `numpy.random`
and `random` states are never used.

The streams are:

- one stream per base graph `(baseline, replicate)`, used for the seed graph and
  phase 1;
- one independent stream per phase-2 network `(baseline, replicate, h2, p2)`,
  including the control.

Phase-2 streams are independent across intervention cells. Common random numbers
are not used (decision D4). The master seed, the derived base seed, and the derived
intervention seed are recorded in the run metadata.

Cascades are deterministic given the network, the threshold `phi`, and the seed
node, because thresholds are homogeneous in the main design and seeds are
enumerated exhaustively. If heterogeneous thresholds are added later, a separate
cascade stream is required.

## 6. Metrics

### 6.1 Network metrics

For every final network:

- number of nodes `N` and number of edges `E`;
- group sizes `n_A`, `n_B`;
- maximum, minimum, mean, and median degree, overall and per group:
  `k_max`, `k_min`, `k_mean`, `k_median`, and the corresponding `A` and `B`
  versions;
- number of cross-group edges and number of within-group edges.

### 6.2 Cascade metrics

For every cascade:

- seed node identifier, group, and degree;
- threshold `phi`;
- cascade size `S_N` and relative size `S_N / N`;
- active counts `S_A` and `S_B`, with the invariant `S_N = S_A + S_B`;
- stopping time `t_s`;
- global-cascade indicator `1[S_N > N/2]`.

### 6.3 Execution metadata

Every run records at least:

- master seed, base seed, and intervention seed;
- model version;
- configuration hash;
- git commit.

The exact CSV columns, types, and `schema_version` belong to
`docs/data-contracts.md`.

### 6.4 Aggregation

For a fixed network and threshold, the seed-level distribution of `S_N`, `t_s`,
`S_A`, and `S_B` is summarized by mean, median, first and third quartiles, and the
fraction of seeds that produce a global cascade. Within-network summaries use all
`N` seeds.

For paired comparisons, the response is the paired difference of the network-level
means defined in Section 5.4. The distribution of these differences is summarized
over the `R` base graphs by mean and median.

For probabilities of global cascades, the frequency is pooled over the relevant
set of `(G0, seed)` pairs. When a per-network fraction is reported, it is the
fraction over the seeds of that network; when a cell-level probability is
reported, it pools all `R` base graphs in the cell.

## 7. Analysis plan

All analyses are descriptive. They report means, medians, correlations, and visual
summaries of paired differences without modeling the dependence structure
explicitly. Formal inference is a later stage.

### 7.1 Heatmap of paired differences

For each baseline `(h1, p1, m)`, each intervention cell, and each threshold `phi`,
compute the mean and median of `Delta S_N` over the `R` base graphs. Display one
figure per baseline, with `h2` on the rows, `p2` on the columns, and one panel per
`phi`. Every cell of the main intervention set is filled, so the map is complete
except for the control cell `(h2, p2) = (h1, p1)`, which is shown as the zero
reference. The behavioral and size profiles are also reported as one-dimensional
plots over `h2` and `p2`, respectively.

### 7.2 Watts heuristic

The heuristic predicts the relative sensitivity to mean-degree versus
maximum-degree seeds by the degree ratio

$$
\hat{\rho} = \frac{\bar{k}}{k_{\max}}.
$$

The empirical counterpart is

$$
\rho = \frac{P(S_N > N/2 \mid \text{mean-degree seed})}
            {P(S_N > N/2 \mid \text{max-degree seed})}.
$$

The two probabilities are pooled frequencies over all `(G0, seed)` pairs in the
cell for a fixed `phi`. The mean-degree class contains all nodes whose degree is
closest to `k_mean`; the maximum-degree class contains all nodes of degree
`k_max`. Ties are averaged, not broken by identifier.

The signed error is `e = rho - rho_hat`, and the absolute error is `|e|`. If the
denominator of `rho` is zero, `rho = NaN` and the number of contributing networks
is reported. The invariant `k_max >= m > 0` does not prevent this case, because the
denominator is a cascade probability, not a degree.

Display one figure per `(h1, h2)` pair, with `m` as panels, `p1` on the rows,
`p2` on the columns, and color given by the mean error over `R` and `phi`. Repeat
per threshold if the error depends strongly on `phi`.

### 7.3 Clustering of cascade regimes

Two separate clusterings are performed, because the coordinates are not
independent. Since `S_N = S_A + S_B`, the group-active counts carry the same
information as the total once the split is known.

- **Dynamics:** feature vector `(S_N, t_s)` per network and threshold, averaged
  over seeds.
- **Composition:** feature vector `(S_A, S_B)` per network and threshold, averaged
  over seeds.

For each clustering: standardize each coordinate, apply PCA and retain enough
components to explain at least 80% of the variance, apply k-means for
`k ∈ {2, ..., 10}`, and choose `k` by the silhouette score. Check stability by
re-running the procedure on random subsets of the base graphs with a recorded
seed. Because the cluster labels are arbitrary, stability is measured by whether
the same cells co-cluster with the same neighbors, not by label identity. Cells
derived from the same `G0` are correlated, so cluster membership is a descriptive
summary, not independent evidence.

Characterize the clusters by the parameters of their cells `(h1, p1, h2, p2, phi,
m)` and by their position on the `(S_N, t_s)` or `(S_A, S_B)` axes.

### 7.4 Directional effect of the intervention

Use `Delta h = h2 - h1` and `Delta p = p2 - p1`. For each pair and each `phi`,
compute the mean and median of `Delta S_N` over `R` and over seeds. Display a
heatmap with `Delta h` on the rows, `Delta p` on the columns, and one panel per
`(m, phi)` pair. The behavioral and size interventions lie on the axes
`Delta p = 0` and `Delta h = 0`, while the mixed interventions fill the interior
of the map.

As a single-number summary, report Pearson and Spearman correlations between
`Delta h` and `Delta S_N`, and between `Delta p` and `Delta S_N`, for each `phi`.
Repeat for `Delta t_s`, `Delta S_A`, and `Delta S_B`. These correlations are
descriptive and are not interpreted as causal effects.

### 7.5 Cascade probability by seed class and group

For each network, threshold, and group `g ∈ {A, B}`, compute the empirical
probability of a global cascade for five seed classes:

1. all nodes in `g` (uniform over the group, exhaustive in practice);
2. nodes whose degree is closest to the mean degree of `g`;
3. nodes whose degree is closest to the median degree of `g`;
4. nodes of maximum degree in `g`;
5. nodes of minimum degree in `g`.

For classes 2 and 3, "closest" means minimum absolute difference. If several
degrees are tied at the minimum distance, all of them are included. For classes 4
and 5, all nodes at the extreme degree are included. The probability for a class
is the fraction of its nodes that produce a global cascade, and the class size is
reported alongside.

Report the five probabilities before and after the intervention, with the control
as reference. Display one figure per group, with the five seed classes on one axis
and the probabilities on the other, with separate series for the intervened
network and its control. Split by `phi` if the pattern depends strongly on the
threshold.

### 7.6 Critical threshold

For each intervention cell, the probability `P(S_N > N/2 | phi)` is evaluated at
the four grid points. Find the first pair of consecutive thresholds
`(phi_lo, phi_hi)` with

$$
P_{lo} < 0.5 \le P_{hi},
$$

and interpolate linearly:

$$
\phi^* = \phi_{lo} + \frac{0.5 - P_{lo}}{P_{hi} - P_{lo}}\,(\phi_{hi} - \phi_{lo}).
$$

If the probability does not cross `0.5` within `Phi`, or if `P_hi = P_lo`, the
critical threshold is reported as not identified. If the probability crosses more
than once, the first crossing is used.

Display one figure per baseline, with `h2` on the rows, `p2` on the columns, and
color given by `phi^*`. The displacement relative to the control cell summarizes
how the intervention shifts the critical threshold: a smaller `phi^*` means the
network is easier to cascade, and a larger `phi^*` means it is harder.

## 8. Decisions

| ID | Decision | Rationale |
|---|---|---|
| D1 | Group assignment is binomial, not an exact quota | Keeps the model as defined by the arrival probability `p`; exact quotas would change the ensemble |
| D2 | Seed graphs depend only on `h1`, with special topologies at `h1 = 0` and `h1 = 1` | Makes the extreme regimes exact and avoids isolated nodes at intermediate values |
| D3 | Attachment uses a degree bag with homophily rejection | Equivalent to the kernel `Pi_i`, fixes the random draw order, and avoids recomputing weights |
| D4 | Phase-2 streams are independent across intervention cells | Simplicity and reproducibility; the paired design already shares `G0` |
| D5 | The main design uses a homogeneous threshold | Avoids a second source of randomness; heterogeneous thresholds are a robustness check |
| D6 | Seeds are enumerated exhaustively, one node per cascade | Captures the full seed-level distribution at `N = 500` |
| D7 | Paired differences are computed at the network level | Phase-2 nodes are not the same node across intervention cells |
| D8 | `h1 = h2 = 1` is kept in the design, with structural zeros documented | The regime is scientifically meaningful even when global cascades are impossible |
| D9 | Degree-class ties are averaged, not broken by identifier | Deterministic and does not discard information |
| D10 | The Watts heuristic reports `NaN` when its denominator is zero | Keeps the analysis honest about undefined ratios |

## 9. Open items

- Heterogeneous thresholds, distribution `f`, restricted robustness subset.
- Formal inference with mixed-effects models or cluster-robust errors.
- Final value of `R` from the power analysis at the level of `G0`.
- Efficient implementation of the cascade engine for 187.5 million cascades.

## 10. References

- Neuhäuser, L., Karimi, F., Bachmann, J., Strohmaier, M., & Schaub, M. T. (2023).
  *Improving the visibility of minorities through network growth interventions*.
  Communications Physics, 6, 108. https://doi.org/10.1038/s42005-023-01218-9
- Watts, D. J. (2002). *A simple model of global cascades on random networks*.
  Proceedings of the National Academy of Sciences, 99(9), 5766–5771.
  https://doi.org/10.1073/pnas.082090499
- Karimi, F., Genois, M., Wagner, C., Singer, P., & Strohmaier, M. (2018).
  *Homophily influences ranking of minorities in social networks*. Scientific
  Reports, 8, 11077. https://doi.org/10.1038/s41598-018-29405-7
