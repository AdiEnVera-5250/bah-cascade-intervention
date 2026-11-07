"""Tests for network-level metrics."""

import pytest

from bah_cascade.growth import (
    GROUP_A,
    GROUP_B,
    Network,
    _to_network,
    build_bipartite_seed,
    build_clique_components_seed,
    build_random_seed,
)
from bah_cascade.metrics import connected_components, network_metrics
from bah_cascade.rng import make_rng


def _path_network() -> Network:
    adjacency = [[1], [0, 2], [1, 3], [2]]
    return _to_network(adjacency, [GROUP_A, GROUP_B, GROUP_A, GROUP_B])


def test_bipartite_metrics_reconcile_edge_types_when_m_is_one() -> None:
    metrics = network_metrics(build_bipartite_seed(1, make_rng(0)))

    assert metrics.n_A == 3
    assert metrics.n_B == 3
    assert metrics.n_edges >= 3
    assert metrics.edges_cross == metrics.n_edges
    assert metrics.edges_within_A == 0
    assert metrics.edges_within_B == 0
    assert metrics.k_min >= 1
    assert metrics.frac_A == 0.5


def test_clique_component_metrics_count_two_components_when_m_is_one() -> None:
    metrics = network_metrics(build_clique_components_seed(1, make_rng(0)))

    assert metrics.n_edges >= 4
    assert metrics.edges_cross == 0
    assert metrics.edges_within_A >= 2
    assert metrics.edges_within_B >= 2
    assert metrics.n_components == 2
    assert metrics.largest_component_size == 3
    assert metrics.k_min >= 1


def test_random_seed_metrics_reconcile_edge_types_when_h1_is_interior() -> None:
    metrics = network_metrics(build_random_seed(1, 0.5, make_rng(0)))

    assert metrics.n_edges == (
        metrics.edges_cross + metrics.edges_within_A + metrics.edges_within_B
    )
    assert metrics.k_min >= 1
    assert metrics.k_max >= metrics.k_min


def test_degree_median_is_mean_of_central_values_when_count_is_even() -> None:
    metrics = network_metrics(_path_network())

    assert metrics.k_median == 1.5


def test_group_degree_summary_matches_hand_computed_values_when_path() -> None:
    metrics = network_metrics(_path_network())

    assert metrics.k_min_A == 1
    assert metrics.k_max_A == 2
    assert metrics.k_mean_A == 1.5
    assert metrics.k_median_A == 1.5
    assert metrics.k_min_B == 1
    assert metrics.k_max_B == 2
    assert metrics.k_mean_B == 1.5
    assert metrics.k_median_B == 1.5


def test_isolated_node_count_is_one_when_node_has_no_neighbors() -> None:
    network = _to_network([[1], [0], []], [GROUP_A, GROUP_B, GROUP_A])

    metrics = network_metrics(network)

    assert metrics.n_isolated == 1
    assert metrics.n_components == 2
    assert metrics.largest_component_size == 2


def test_connected_components_return_smallest_node_first_when_disconnected() -> None:
    network = _to_network([[1], [0], [3], [2]], [GROUP_A, GROUP_B, GROUP_A, GROUP_B])

    assert connected_components(network) == ((0, 1), (2, 3))


def test_network_metrics_reject_empty_group_when_constructed() -> None:
    network = _to_network([[1], [0]], [GROUP_A, GROUP_A])

    with pytest.raises(ValueError):
        network_metrics(network)
