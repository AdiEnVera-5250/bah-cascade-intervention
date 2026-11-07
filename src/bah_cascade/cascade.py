"""Synchronous threshold cascades with exhaustive single-node seeds."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bah_cascade.growth import GROUP_A, GROUP_B, Network


@dataclass(frozen=True, slots=True)
class CascadeResult:
    """Steady-state summary of one cascade."""

    seed_id: int
    phi: float
    S_N: int
    S_A: int
    S_B: int
    t_s: int
    is_global: bool


def _validate_phi(phi: float) -> None:
    if not 0.0 <= phi <= 1.0:
        raise ValueError(f"phi must lie in [0, 1], got {phi!r}")


def _simulate(
    network: Network,
    seed_id: int,
    phi: float,
    degrees: np.ndarray,
    thresholds: np.ndarray,
) -> CascadeResult:
    n_nodes = network.n_nodes
    active = np.zeros(n_nodes, dtype=bool)
    active_neighbors = np.zeros(n_nodes, dtype=np.int32)
    active[seed_id] = True
    frontier = np.asarray([seed_id], dtype=np.int32)
    t_s = 0

    while frontier.size:
        starts = network.indptr[frontier]
        ends = network.indptr[frontier + 1]
        for start, end in zip(starts, ends, strict=True):
            np.add.at(active_neighbors, network.indices[start:end], 1)

        candidates = np.flatnonzero((~active) & (degrees > 0) & (active_neighbors >= thresholds))
        if candidates.size == 0:
            break
        active[candidates] = True
        frontier = candidates
        t_s += 1

    active_counts = np.bincount(network.groups[active], minlength=2)
    s_a = int(active_counts[GROUP_A])
    s_b = int(active_counts[GROUP_B])
    s_n = s_a + s_b
    return CascadeResult(
        seed_id=seed_id,
        phi=phi,
        S_N=s_n,
        S_A=s_a,
        S_B=s_b,
        t_s=t_s,
        is_global=2 * s_n > n_nodes,
    )


def run_cascade(network: Network, seed_id: int, phi: float) -> CascadeResult:
    """Run one synchronous cascade from ``seed_id`` at threshold ``phi``."""
    _validate_phi(phi)
    if not 0 <= seed_id < network.n_nodes:
        raise IndexError("seed_id is outside the network")
    degrees = network.degrees()
    thresholds = np.ceil(phi * degrees).astype(np.int32)
    return _simulate(network, seed_id, phi, degrees, thresholds)


def simulate_all_seeds(network: Network, phi: float) -> tuple[CascadeResult, ...]:
    """Run one cascade per node, in ascending seed order."""
    _validate_phi(phi)
    degrees = network.degrees()
    thresholds = np.ceil(phi * degrees).astype(np.int32)
    return tuple(
        _simulate(network, seed_id, phi, degrees, thresholds) for seed_id in range(network.n_nodes)
    )
