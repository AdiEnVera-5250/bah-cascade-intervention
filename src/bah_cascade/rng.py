"""Deterministic random streams derived from a master seed."""

from __future__ import annotations

import numpy as np

FLOAT_KEY_SCALE = 1_000_000_000

DOMAIN_BASE = 1
DOMAIN_INTERVENTION = 2


def _validate_probability(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1], got {value!r}")


def _float_key(value: float) -> int:
    """Encode a probability as a non-negative integer SeedSequence key."""
    return int(round(value * FLOAT_KEY_SCALE))


def derive_seed(master_seed: int, *keys: int) -> int:
    """Derive an integer seed from the master seed and explicit stream keys."""
    if master_seed < 0:
        raise ValueError("master_seed must be non-negative")
    if any(key < 0 for key in keys):
        raise ValueError("stream keys must be non-negative")
    sequence = np.random.SeedSequence(entropy=master_seed, spawn_key=keys)
    return int(sequence.generate_state(1, dtype=np.uint64)[0])


def make_rng(seed: int) -> np.random.Generator:
    """Build an explicit generator from a recorded integer seed."""
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return np.random.default_rng(seed)


def base_seed(
    master_seed: int,
    m: int,
    h1: float,
    p1: float,
    replicate: int,
) -> int:
    """Derive the stream seed for one base graph and its phase-1 growth."""
    if m < 1:
        raise ValueError("m must be at least 1")
    if replicate < 1:
        raise ValueError("replicate must be at least 1")
    _validate_probability(h1, "h1")
    _validate_probability(p1, "p1")
    return derive_seed(
        master_seed,
        DOMAIN_BASE,
        m,
        _float_key(h1),
        _float_key(p1),
        replicate,
    )


def intervention_seed(
    master_seed: int,
    m: int,
    h1: float,
    p1: float,
    replicate: int,
    h2: float,
    p2: float,
) -> int:
    """Derive the independent phase-2 stream seed for one network."""
    if m < 1:
        raise ValueError("m must be at least 1")
    if replicate < 1:
        raise ValueError("replicate must be at least 1")
    _validate_probability(h1, "h1")
    _validate_probability(p1, "p1")
    _validate_probability(h2, "h2")
    _validate_probability(p2, "p2")
    return derive_seed(
        master_seed,
        DOMAIN_INTERVENTION,
        m,
        _float_key(h1),
        _float_key(p1),
        replicate,
        _float_key(h2),
        _float_key(p2),
    )
