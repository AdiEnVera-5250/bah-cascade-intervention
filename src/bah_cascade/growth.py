"""Network growth with homophily and a degree bag."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

GROUP_A = 0
GROUP_B = 1


def _validate_probability(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1], got {value!r}")


def _validate_m(m: int) -> None:
    if m < 1:
        raise ValueError("m must be at least 1")


def _validate_csr(indptr: np.ndarray, indices: np.ndarray, groups: np.ndarray) -> None:
    if indptr.ndim != 1 or indptr.size == 0:
        raise ValueError("indptr must be a non-empty one-dimensional array")
    if indptr[0] != 0:
        raise ValueError("indptr must start at zero")
    if np.any(indptr[1:] < indptr[:-1]):
        raise ValueError("indptr must be non-decreasing")
    if indices.ndim != 1:
        raise ValueError("indices must be one-dimensional")
    if groups.ndim != 1:
        raise ValueError("groups must be one-dimensional")
    n_nodes = groups.size
    if n_nodes == 0:
        raise ValueError("a network must contain at least one node")
    if indptr.size != n_nodes + 1:
        raise ValueError("indptr length must equal the number of nodes plus one")
    if indptr[-1] != indices.size:
        raise ValueError("indptr must end at the number of indices")
    if indices.size % 2 != 0:
        raise ValueError("an undirected network must have an even number of stubs")
    if np.any((groups != GROUP_A) & (groups != GROUP_B)):
        raise ValueError("groups must be 0 (A) or 1 (B)")
    if indices.size and (indices.min() < 0 or indices.max() >= n_nodes):
        raise ValueError("indices contain an out-of-range node identifier")

    adjacency: list[set[int]] = []
    for node in range(n_nodes):
        neighbors = set(indices[indptr[node] : indptr[node + 1]].tolist())
        if node in neighbors:
            raise ValueError("self-loops are not allowed")
        if len(neighbors) != indptr[node + 1] - indptr[node]:
            raise ValueError("multiple edges are not allowed")
        adjacency.append(neighbors)

    for node, neighbors in enumerate(adjacency):
        for neighbor in neighbors:
            if node not in adjacency[neighbor]:
                raise ValueError("the adjacency structure must be symmetric")


@dataclass(frozen=True, slots=True)
class Network:
    """Immutable network stored as a compressed sparse row structure."""

    indptr: np.ndarray
    indices: np.ndarray
    groups: np.ndarray

    def __post_init__(self) -> None:
        indptr = np.array(self.indptr, dtype=np.int32, copy=True)
        indices = np.array(self.indices, dtype=np.int32, copy=True)
        groups = np.array(self.groups, dtype=np.int8, copy=True)
        _validate_csr(indptr, indices, groups)
        for array in (indptr, indices, groups):
            array.setflags(write=False)
        object.__setattr__(self, "indptr", indptr)
        object.__setattr__(self, "indices", indices)
        object.__setattr__(self, "groups", groups)

    @property
    def n_nodes(self) -> int:
        return int(self.groups.size)

    @property
    def n_edges(self) -> int:
        return int(self.indices.size // 2)

    def degrees(self) -> np.ndarray:
        """Return the degree of every node in identifier order."""
        return np.diff(self.indptr)

    def neighbors(self, node: int) -> np.ndarray:
        """Return the neighbors of ``node`` in ascending order."""
        return self.indices[self.indptr[node] : self.indptr[node + 1]]


def _to_network(adjacency: list[list[int]], groups: list[int]) -> Network:
    n_nodes = len(adjacency)
    indptr = np.zeros(n_nodes + 1, dtype=np.int32)
    for node, neighbors in enumerate(adjacency):
        indptr[node + 1] = indptr[node] + len(neighbors)

    indices = np.empty(int(indptr[-1]), dtype=np.int32)
    for node, neighbors in enumerate(adjacency):
        if neighbors:
            indices[indptr[node] : indptr[node + 1]] = np.sort(
                np.asarray(neighbors, dtype=np.int32)
            )
    return Network(indptr, indices, np.asarray(groups, dtype=np.int8))


def _bag_from_adjacency(adjacency: list[list[int]]) -> list[int]:
    bag: list[int] = []
    for node, neighbors in enumerate(adjacency):
        bag.extend([node] * len(neighbors))
    return bag


def _random_seed_adjacency(
    m: int,
    h1: float,
    rng: np.random.Generator,
) -> tuple[list[list[int]], list[int]]:
    n_side = m + 2
    n_nodes = 2 * n_side
    labels = np.asarray([GROUP_A] * n_side + [GROUP_B] * n_side, dtype=np.int8)
    rng.shuffle(labels)
    groups = labels.tolist()

    adjacency: list[set[int]] = [set() for _ in range(n_nodes)]
    for node in rng.permutation(n_nodes).tolist():
        while len(adjacency[node]) < m:
            same_group = [
                other
                for other in range(n_nodes)
                if other != node and other not in adjacency[node] and groups[other] == groups[node]
            ]
            cross_group = [
                other
                for other in range(n_nodes)
                if other != node and other not in adjacency[node] and groups[other] != groups[node]
            ]

            if h1 == 0.0:
                candidates = cross_group
            elif h1 == 1.0:
                candidates = same_group
            else:
                prefer_same_group = rng.random() < h1
                candidates = same_group if prefer_same_group else cross_group
                if not candidates:
                    candidates = cross_group if prefer_same_group else same_group

            if not candidates:
                raise RuntimeError("seed graph cannot satisfy the minimum degree")
            partner = candidates[int(rng.integers(0, len(candidates)))]
            adjacency[node].add(partner)
            adjacency[partner].add(node)

    return [sorted(neighbors) for neighbors in adjacency], groups


def build_bipartite_seed(m: int, rng: np.random.Generator) -> Network:
    """Build a random bipartite seed graph with minimum degree ``m``."""
    _validate_m(m)
    adjacency, groups = _random_seed_adjacency(m, 0.0, rng)
    return _to_network(adjacency, groups)


def build_clique_components_seed(m: int, rng: np.random.Generator) -> Network:
    """Build the ``h1 = 1`` seed graph: two complete group components."""
    _validate_m(m)
    adjacency, groups = _random_seed_adjacency(m, 1.0, rng)
    return _to_network(adjacency, groups)


def build_random_seed(m: int, h1: float, rng: np.random.Generator) -> Network:
    """Build a random seed graph with minimum degree ``m`` and homophily ``h1``."""
    _validate_m(m)
    _validate_probability(h1, "h1")
    adjacency, groups = _random_seed_adjacency(m, h1, rng)
    return _to_network(adjacency, groups)


def build_seed_graph(m: int, h1: float, rng: np.random.Generator) -> Network:
    """Build a random seed graph with minimum degree ``m``."""
    _validate_m(m)
    _validate_probability(h1, "h1")
    if h1 == 0.0:
        return build_bipartite_seed(m, rng)
    if h1 == 1.0:
        return build_clique_components_seed(m, rng)
    return build_random_seed(m, h1, rng)


def _attach_node(
    adjacency: list[list[int]],
    groups: list[int],
    bag: list[int],
    m: int,
    h: float,
    p: float,
    rng: np.random.Generator,
) -> int:
    group = GROUP_A if rng.random() < p else GROUP_B
    used: set[int] = set()
    chosen: list[int] = []

    while len(chosen) < m:
        candidate = bag[int(rng.integers(0, len(bag)))]
        if candidate in used:
            continue
        accept = h if groups[candidate] == group else 1.0 - h
        if rng.random() >= accept:
            continue
        used.add(candidate)
        chosen.append(candidate)

    node = len(adjacency)
    for candidate in chosen:
        adjacency[candidate].append(node)
    adjacency.append(list(chosen))
    groups.append(group)
    bag.extend([node] * m)
    bag.extend(chosen)
    return node


def _grow_in_place(
    adjacency: list[list[int]],
    groups: list[int],
    bag: list[int],
    m: int,
    target_n: int,
    h: float,
    p: float,
    rng: np.random.Generator,
) -> None:
    while len(adjacency) < target_n:
        _attach_node(adjacency, groups, bag, m, h, p, rng)


def grow_to(
    network: Network,
    m: int,
    target_n: int,
    h: float,
    p: float,
    rng: np.random.Generator,
) -> Network:
    """Continue growth from ``network`` until it has ``target_n`` nodes."""
    _validate_m(m)
    _validate_probability(h, "h")
    _validate_probability(p, "p")
    if target_n < network.n_nodes:
        raise ValueError("target_n must not be smaller than the current network")

    adjacency = [network.neighbors(node).tolist() for node in range(network.n_nodes)]
    groups = network.groups.tolist()
    bag = _bag_from_adjacency(adjacency)
    _grow_in_place(adjacency, groups, bag, m, target_n, h, p, rng)
    return _to_network(adjacency, groups)


def grow_phase1(
    m: int,
    h1: float,
    p1: float,
    n1: int,
    rng: np.random.Generator,
) -> Network:
    """Build the seed graph and grow it to ``n1`` nodes."""
    _validate_m(m)
    _validate_probability(h1, "h1")
    _validate_probability(p1, "p1")
    if n1 < 2 * (m + 2):
        raise ValueError("n1 must fit the seed graph")
    seed = build_seed_graph(m, h1, rng)
    return grow_to(seed, m, n1, h1, p1, rng)


def grow_phase2(
    g0: Network,
    m: int,
    h2: float,
    p2: float,
    n2: int,
    rng: np.random.Generator,
) -> Network:
    """Continue growth from ``g0`` by ``n2`` nodes under the phase-2 parameters."""
    if n2 < 0:
        raise ValueError("n2 must be non-negative")
    return grow_to(g0, m, g0.n_nodes + n2, h2, p2, rng)
