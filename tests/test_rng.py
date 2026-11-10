"""Tests for deterministic random-stream derivation."""

import numpy as np
import pytest

from bah_cascade.growth import grow_phase1
from bah_cascade.rng import base_seed, derive_seed, intervention_seed, make_rng


def test_derive_seed_separates_domains_when_first_key_differs() -> None:
    assert derive_seed(123, 1, 2) != derive_seed(123, 2, 2)


def test_intervention_seed_differs_from_base_seed_when_keys_differ() -> None:
    base = base_seed(7, 1, 0.8, 0.4, 1)
    intervention = intervention_seed(7, 1, 0.8, 0.4, 1, 0.2, 0.4)

    assert base != intervention


def test_base_network_is_reproducible_from_recorded_base_seed_when_rebuilt() -> None:
    seed = base_seed(7, 1, 0.8, 0.4, 1)
    first = grow_phase1(1, 0.8, 0.4, 20, make_rng(seed))
    second = grow_phase1(1, 0.8, 0.4, 20, make_rng(seed))

    assert np.array_equal(first.indptr, second.indptr)
    assert np.array_equal(first.indices, second.indices)
    assert np.array_equal(first.groups, second.groups)


@pytest.mark.parametrize(
    "override",
    [{"m": 2}, {"h1": 0.5}, {"p1": 0.6}, {"replicate": 2}],
    ids=["m", "h1", "p1", "replicate"],
)
def test_base_seed_changes_when_one_baseline_key_differs(
    override: dict[str, int | float],
) -> None:
    baseline: dict[str, int | float] = {
        "master_seed": 7,
        "m": 1,
        "h1": 0.8,
        "p1": 0.4,
        "replicate": 1,
    }

    assert base_seed(**baseline) != base_seed(**(baseline | override))


@pytest.mark.parametrize(
    "override",
    [{"h2": 0.5}, {"p2": 0.6}],
    ids=["h2", "p2"],
)
def test_intervention_seed_changes_when_one_target_key_differs(
    override: dict[str, float],
) -> None:
    baseline: dict[str, int | float] = {
        "master_seed": 7,
        "m": 1,
        "h1": 0.8,
        "p1": 0.4,
        "replicate": 1,
        "h2": 0.2,
        "p2": 0.4,
    }

    assert intervention_seed(**baseline) != intervention_seed(**(baseline | override))
