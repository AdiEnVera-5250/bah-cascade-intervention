"""Network-level metrics computed from a CSR network."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bah_cascade.growth import GROUP_A, GROUP_B, Network


@dataclass(frozen=True, slots=True)
class NetworkMetrics:
    """Network metrics required by ``networks.csv``."""

    n_A: int
    n_B: int
    n_isolated: int
    n_edges: int
    edges_cross: int
    edges_within_A: int
    edges_within_B: int
    n_components: int
    largest_component_size: int
    k_min: int
    k_max: int
    k_mean: float
    k_median: float
    k_min_A: int
    k_max_A: int
    k_mean_A: float
    k_median_A: float
    k_min_B: int
    k_max_B: int
    k_mean_B: float
    k_median_B: float
    frac_A: float


def connected_components(network: Network) -> tuple[tuple[int, ...], ...]:
    """Return connected components in ascending order of their smallest node."""
    visited = np.zeros(network.n_nodes, dtype=bool)
    components: list[tuple[int, ...]] = []

    for start in range(network.n_nodes):
        if visited[start]:
            continue
        visited[start] = True
        stack = [start]
        component: list[int] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in network.neighbors(node):
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append(int(neighbor))
        components.append(tuple(sorted(component)))

    return tuple(components)


def _degree_summary(degrees: np.ndarray) -> tuple[int, int, float, float]:
    return (
        int(degrees.min()),
        int(degrees.max()),
        float(degrees.mean()),
        float(np.median(degrees)),
    )


def network_metrics(network: Network) -> NetworkMetrics:
    """Compute every network-level metric in the data contract."""
    degrees = network.degrees()
    groups = network.groups
    n_nodes = network.n_nodes

    n_a = int(np.count_nonzero(groups == GROUP_A))
    n_b = int(np.count_nonzero(groups == GROUP_B))
    if n_a == 0 or n_b == 0:
        raise ValueError("both groups must be non-empty")

    edges_cross = 0
    edges_within_a = 0
    edges_within_b = 0
    for node in range(n_nodes):
        neighbors = network.neighbors(node)
        same_group = groups[neighbors] == groups[node]
        if groups[node] == GROUP_A:
            edges_within_a += int(np.count_nonzero(same_group))
        else:
            edges_within_b += int(np.count_nonzero(same_group))
        edges_cross += int(np.count_nonzero(~same_group))

    edges_cross //= 2
    edges_within_a //= 2
    edges_within_b //= 2

    components = connected_components(network)
    degrees_a = degrees[groups == GROUP_A]
    degrees_b = degrees[groups == GROUP_B]
    k_min_a, k_max_a, k_mean_a, k_median_a = _degree_summary(degrees_a)
    k_min_b, k_max_b, k_mean_b, k_median_b = _degree_summary(degrees_b)

    return NetworkMetrics(
        n_A=n_a,
        n_B=n_b,
        n_isolated=int(np.count_nonzero(degrees == 0)),
        n_edges=network.n_edges,
        edges_cross=edges_cross,
        edges_within_A=edges_within_a,
        edges_within_B=edges_within_b,
        n_components=len(components),
        largest_component_size=max(len(component) for component in components),
        k_min=int(degrees.min()),
        k_max=int(degrees.max()),
        k_mean=float(degrees.mean()),
        k_median=float(np.median(degrees)),
        k_min_A=k_min_a,
        k_max_A=k_max_a,
        k_mean_A=k_mean_a,
        k_median_A=k_median_a,
        k_min_B=k_min_b,
        k_max_B=k_max_b,
        k_mean_B=k_mean_b,
        k_median_B=k_median_b,
        frac_A=n_a / n_nodes,
    )
