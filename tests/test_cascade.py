"""Tests for synchronous threshold cascades."""

import numpy as np

from bah_cascade.cascade import run_cascade, simulate_all_seeds
from bah_cascade.growth import GROUP_A, GROUP_B, Network, _to_network


def _network_from_edges(
    n_nodes: int,
    edges: list[tuple[int, int]],
    groups: list[int],
) -> Network:
    adjacency: list[list[int]] = [[] for _ in range(n_nodes)]
    for left, right in edges:
        adjacency[left].append(right)
        adjacency[right].append(left)
    return _to_network(adjacency, groups)


def test_path_cascade_reaches_all_nodes_when_phi_is_half() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (1, 2), (2, 3)],
        [GROUP_A, GROUP_B, GROUP_A, GROUP_B],
    )

    result = run_cascade(network, 0, 0.5)

    assert result.S_N == 4
    assert result.S_A == 2
    assert result.S_B == 2
    assert result.t_s == 3
    assert result.is_global


def test_star_leaf_seed_stays_isolated_when_phi_is_half() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (0, 2), (0, 3)],
        [GROUP_A, GROUP_B, GROUP_B, GROUP_B],
    )

    result = run_cascade(network, 1, 0.5)

    assert result.S_N == 1
    assert result.t_s == 0
    assert not result.is_global


def test_star_center_seed_activates_every_leaf_when_phi_is_half() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (0, 2), (0, 3)],
        [GROUP_A, GROUP_B, GROUP_B, GROUP_B],
    )

    result = run_cascade(network, 0, 0.5)

    assert result.S_N == 4
    assert result.t_s == 1
    assert result.is_global


def test_isolated_seed_stays_inactive_when_degree_is_zero() -> None:
    network = _network_from_edges(2, [], [GROUP_A, GROUP_B])

    result = run_cascade(network, 0, 0.0)

    assert result.S_N == 1
    assert result.t_s == 0
    assert not result.is_global


def test_cascade_activates_every_positive_degree_node_when_phi_is_zero() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (1, 2), (2, 3)],
        [GROUP_A, GROUP_B, GROUP_A, GROUP_B],
    )

    result = run_cascade(network, 0, 0.0)

    assert result.S_N == 4
    assert result.t_s == 1


def test_cascade_is_not_global_when_half_the_network_is_active() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (2, 3)],
        [GROUP_A, GROUP_B, GROUP_A, GROUP_B],
    )

    result = run_cascade(network, 0, 0.5)

    assert result.S_N == 2
    assert not result.is_global


def test_cascade_is_global_when_three_of_four_nodes_are_active() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (1, 2), (2, 0)],
        [GROUP_A, GROUP_B, GROUP_A, GROUP_B],
    )

    result = run_cascade(network, 0, 0.5)

    assert result.S_N == 3
    assert result.is_global


def test_simulate_all_seeds_returns_one_result_per_node_when_exhaustive() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (1, 2), (2, 3)],
        [GROUP_A, GROUP_B, GROUP_A, GROUP_B],
    )

    results = simulate_all_seeds(network, 0.5)

    assert [result.seed_id for result in results] == [0, 1, 2, 3]
    assert all(result.S_N == result.S_A + result.S_B for result in results)


def test_run_cascade_does_not_mutate_the_network_when_executed() -> None:
    network = _network_from_edges(
        4,
        [(0, 1), (1, 2), (2, 3)],
        [GROUP_A, GROUP_B, GROUP_A, GROUP_B],
    )
    indptr = network.indptr.copy()
    indices = network.indices.copy()
    groups = network.groups.copy()

    run_cascade(network, 0, 0.5)

    assert np.array_equal(network.indptr, indptr)
    assert np.array_equal(network.indices, indices)
    assert np.array_equal(network.groups, groups)
