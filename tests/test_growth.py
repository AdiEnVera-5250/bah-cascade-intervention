"""Tests for seed-graph construction and two-phase growth."""

import numpy as np
import pytest

from bah_cascade.growth import (
    GROUP_A,
    GROUP_B,
    Network,
    _attach_node,
    _bag_from_adjacency,
    build_bipartite_seed,
    build_clique_components_seed,
    build_random_seed,
    build_seed_graph,
    grow_phase1,
    grow_phase2,
    grow_to,
)
from bah_cascade.metrics import network_metrics
from bah_cascade.rng import make_rng


def _assert_simple_network(network: Network) -> None:
    for node in range(network.n_nodes):
        neighbors = network.neighbors(node).tolist()
        assert node not in neighbors
        assert len(neighbors) == len(set(neighbors))
        for neighbor in neighbors:
            assert node in network.neighbors(neighbor)


def test_bipartite_seed_has_minimum_degree_when_m_is_one() -> None:
    network = build_bipartite_seed(1, make_rng(0))
    metrics = network_metrics(network)

    assert network.n_nodes == 4
    assert np.all(network.degrees() >= 1)
    assert metrics.edges_cross == network.n_edges
    assert metrics.edges_within_A == 0
    assert metrics.edges_within_B == 0


def test_clique_component_seed_has_two_edges_when_m_is_one() -> None:
    network = build_clique_components_seed(1, make_rng(0))
    metrics = network_metrics(network)

    assert network.n_nodes == 4
    assert network.n_edges == 2
    assert metrics.edges_cross == 0
    assert metrics.edges_within_A == 1
    assert metrics.edges_within_B == 1
    assert metrics.n_components == 2
    assert np.all(network.degrees() == 1)


def test_clique_component_seed_is_complete_when_m_is_two() -> None:
    network = build_clique_components_seed(2, make_rng(0))
    metrics = network_metrics(network)

    assert network.n_nodes == 6
    assert network.n_edges == 6
    assert metrics.edges_cross == 0
    assert metrics.edges_within_A == 3
    assert metrics.edges_within_B == 3
    assert metrics.n_components == 2
    assert np.all(network.degrees() == 2)


def test_bipartite_seed_varies_with_seed_when_m_is_two() -> None:
    first = build_bipartite_seed(2, make_rng(0))
    second = build_bipartite_seed(2, make_rng(1))

    same = (
        np.array_equal(first.indptr, second.indptr)
        and np.array_equal(first.indices, second.indices)
        and np.array_equal(first.groups, second.groups)
    )
    assert not same


def test_random_seed_has_minimum_degree_when_h1_is_interior() -> None:
    network = build_random_seed(2, 0.5, make_rng(0))

    assert network.n_nodes == 6
    assert np.all(network.degrees() >= 2)
    _assert_simple_network(network)


@pytest.mark.parametrize("h1", [0.0, 0.2, 0.5, 1.0])
def test_seed_graph_keeps_minimum_degree_when_m_is_two(h1: float) -> None:
    network = build_seed_graph(2, h1, make_rng(3))

    assert np.all(network.degrees() >= 2)


@pytest.mark.parametrize("h1", [0.0, 0.2, 1.0])
def test_seed_graph_assigns_two_nodes_per_group_when_m_is_one(h1: float) -> None:
    network = build_seed_graph(1, h1, make_rng(3))

    assert np.count_nonzero(network.groups == GROUP_A) == 2
    assert np.count_nonzero(network.groups == GROUP_B) == 2


@pytest.mark.parametrize("h1", [0.0, 0.2, 1.0])
def test_seed_graph_has_no_self_loops_or_multiple_edges_when_m_is_two(h1: float) -> None:
    _assert_simple_network(build_seed_graph(2, h1, make_rng(4)))


def test_growth_produces_requested_node_count_when_phase_runs() -> None:
    network = grow_phase1(1, 0.2, 0.4, 30, make_rng(5))

    assert network.n_nodes == 30


def test_growth_keeps_minimum_degree_when_phase_runs() -> None:
    network = grow_phase1(2, 0.2, 0.4, 30, make_rng(6))

    assert np.all(network.degrees() >= 2)


def test_growth_keeps_degree_bag_equal_to_degrees_when_nodes_arrive() -> None:
    m = 1
    rng = make_rng(7)
    seed = build_seed_graph(m, 0.2, rng)
    adjacency = [seed.neighbors(node).tolist() for node in range(seed.n_nodes)]
    groups = seed.groups.tolist()
    bag = _bag_from_adjacency(adjacency)

    for _ in range(10):
        _attach_node(adjacency, groups, bag, m, 0.2, 0.4, rng)
        degrees = np.asarray([len(neighbors) for neighbors in adjacency])
        counts = np.bincount(bag, minlength=len(adjacency))

        assert np.array_equal(counts, degrees)
        assert len(bag) == int(degrees.sum())


def test_growth_is_reproducible_when_seed_is_repeated() -> None:
    first = grow_phase1(2, 0.5, 0.4, 25, make_rng(8))
    second = grow_phase1(2, 0.5, 0.4, 25, make_rng(8))

    assert np.array_equal(first.indptr, second.indptr)
    assert np.array_equal(first.indices, second.indices)
    assert np.array_equal(first.groups, second.groups)


def test_phase2_preserves_base_subgraph_when_intervention_differs() -> None:
    g0 = grow_phase1(1, 0.5, 0.4, 20, make_rng(9))
    g2 = grow_phase2(g0, 1, 0.2, 0.4, 10, make_rng(10))

    for node in range(g0.n_nodes):
        base_neighbors = g0.neighbors(node)
        phase2_neighbors = g2.neighbors(node)
        kept = phase2_neighbors[phase2_neighbors < g0.n_nodes]

        assert np.array_equal(base_neighbors, kept)


def test_phase2_has_no_cross_group_edges_when_h_is_one() -> None:
    g0 = grow_phase1(2, 1.0, 0.4, 20, make_rng(11))
    g2 = grow_phase2(g0, 2, 1.0, 0.6, 10, make_rng(12))

    assert network_metrics(g2).edges_cross == 0


def test_phase2_has_only_cross_group_edges_when_h_is_zero() -> None:
    g0 = grow_phase1(2, 0.0, 0.4, 20, make_rng(13))
    g2 = grow_phase2(g0, 2, 0.0, 0.6, 10, make_rng(14))
    metrics = network_metrics(g2)

    assert metrics.edges_within_A == 0
    assert metrics.edges_within_B == 0


def test_grow_to_rejects_smaller_target_when_called() -> None:
    network = grow_phase1(1, 0.8, 0.4, 12, make_rng(15))

    with pytest.raises(ValueError):
        grow_to(network, 1, 11, 0.8, 0.4, make_rng(16))


def test_build_seed_graph_rejects_homophily_below_zero_when_called() -> None:
    with pytest.raises(ValueError):
        build_seed_graph(1, -0.1, make_rng(17))


def test_to_network_rejects_duplicate_edges_when_constructed() -> None:
    with pytest.raises(ValueError):
        Network(
            indptr=np.asarray([0, 2, 4, 4, 4]),
            indices=np.asarray([1, 1, 0, 0]),
            groups=np.asarray([GROUP_A, GROUP_B, GROUP_A, GROUP_B]),
        )
