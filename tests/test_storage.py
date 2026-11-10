"""Tests for deterministic storage and serialization."""

from pathlib import Path

import pandas as pd
import pytest

from bah_cascade.storage import (
    NETWORK_COLUMNS,
    baseline_id,
    read_networks,
    write_cascades,
    write_networks,
)


def _network_row(
    network_id: int = 1,
    control_network_id: int | None = None,
) -> dict[str, object]:
    row = {column: 0 for column in NETWORK_COLUMNS}
    row.update(
        {
            "network_id": network_id,
            "baseline_id": "m1_h0.8_p0.4",
            "replicate": 1,
            "intervention_type": "none",
            "control_network_id": control_network_id,
            "h1": 0.8,
            "p1": 0.4,
            "h2": 0.8,
            "p2": 0.4,
            "m": 1,
            "N1": 20,
            "N2": 10,
            "N": 30,
            "base_seed": 2**63 + 5,
            "intervention_seed": 2**63 + 6,
            "n_A": 12,
            "n_B": 18,
            "n_edges": 29,
            "n_components": 1,
            "largest_component_size": 30,
            "k_min": 1,
            "k_max": 7,
            "k_mean": 58 / 30,
            "k_median": 1.0,
            "k_min_A": 1,
            "k_max_A": 7,
            "k_mean_A": 1.5,
            "k_median_A": 1.0,
            "k_min_B": 1,
            "k_max_B": 7,
            "k_mean_B": 1.5,
            "k_median_B": 1.0,
            "frac_A": 0.4,
        }
    )
    return row


def _cascade_row(seed_id: int, phi: float) -> dict[str, object]:
    return {
        "network_id": 1,
        "seed_id": seed_id,
        "seed_group": "A",
        "seed_degree": 2,
        "seed_stage": "base",
        "seed_component_size": 30,
        "phi": phi,
        "S_N": 3,
        "S_A": 2,
        "S_B": 1,
        "S_N_rel": 0.1,
        "t_s": 2,
        "is_global": 0,
    }


def test_baseline_id_uses_shortest_round_trip_when_h_is_one() -> None:
    assert baseline_id(1, 1.0, 0.4) == "m1_h1.0_p0.4"


def test_write_networks_uses_lf_without_bom_when_written(tmp_path: Path) -> None:
    path = tmp_path / "networks.csv"

    write_networks(path, [_network_row()])

    data = path.read_bytes()
    assert data.startswith(b"network_id,")
    assert b"\r\n" not in data
    assert not data.startswith(b"\xef\xbb\xbf")
    assert data.endswith(b"\n")


def test_write_cascades_is_byte_identical_when_written_twice(tmp_path: Path) -> None:
    rows = [_cascade_row(0, 0.1), _cascade_row(1, 0.1)]
    first = tmp_path / "first.csv.gz"
    second = tmp_path / "second.csv.gz"

    write_cascades(first, rows)
    write_cascades(second, rows)

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes()[4:8] == b"\x00\x00\x00\x00"


def test_read_networks_preserves_nullable_control_id_when_control_has_no_fk(
    tmp_path: Path,
) -> None:
    path = tmp_path / "networks.csv"
    write_networks(path, [_network_row(1), _network_row(2, 1)])

    frame = read_networks(path)

    assert pd.isna(frame.loc[0, "control_network_id"])
    assert int(frame.loc[1, "control_network_id"]) == 1


def test_write_networks_rejects_unsorted_rows_when_ids_decrease(tmp_path: Path) -> None:
    path = tmp_path / "networks.csv"

    with pytest.raises(ValueError):
        write_networks(path, [_network_row(2), _network_row(1)])


def test_write_cascades_rejects_unsorted_rows_when_key_decreases(tmp_path: Path) -> None:
    path = tmp_path / "cascades.csv.gz"

    with pytest.raises(ValueError):
        write_cascades(path, [_cascade_row(2, 0.1), _cascade_row(1, 0.1)])
