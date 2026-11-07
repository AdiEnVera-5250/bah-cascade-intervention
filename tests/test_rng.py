"""Tests for deterministic random-stream derivation."""

import numpy as np

from bah_cascade.growth import grow_phase1
from bah_cascade.rng import base_seed, derive_seed, intervention_seed, make_rng


def test_derive_seed_is_deterministic_when_keys_repeat() -> None:
    assert derive_seed(123, 1, 2) == derive_seed(123, 1, 2)


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
