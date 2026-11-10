"""Integration tests for the experiment runner."""

import shutil
from pathlib import Path

import pandas as pd
import pytest

from bah_cascade.config import SMOKE
from bah_cascade.runner import run
from bah_cascade.storage import (
    ContractError,
    count_rows,
    read_cascades,
    read_metadata,
    read_networks,
    sha256_file,
    validate_run,
    write_metadata,
    write_networks,
)

SEED = 20261108


def _run_smoke(tmp_path: Path, seed: int = SEED) -> Path:
    return run(seed, SMOKE, tmp_path)


def _partition(run_dir: Path) -> Path:
    return next((run_dir / "cascades").glob("*.csv.gz"))


def test_run_writes_two_networks_and_sixty_cascades_when_smoke_config(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)

    report = validate_run(run_dir)

    assert report.networks == 2
    assert report.cascades == 60


def test_run_assigns_network_ids_in_contract_order_when_smoke_config(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)

    frame = read_networks(run_dir / "networks.csv")

    assert frame["network_id"].tolist() == [1, 2]
    assert frame["intervention_type"].tolist() == ["behavioral", "none"]
    assert int(frame.loc[0, "control_network_id"]) == 2
    assert pd.isna(frame.loc[1, "control_network_id"])


def test_run_shares_base_seed_between_control_and_intervention_when_same_g0(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)

    frame = read_networks(run_dir / "networks.csv")

    assert frame["base_seed"].nunique() == 1
    assert frame["intervention_seed"].nunique() == 2


def test_run_uses_seed_in_run_id_when_two_seeds_are_executed(tmp_path: Path) -> None:
    first = _run_smoke(tmp_path, seed=1)
    second = _run_smoke(tmp_path, seed=2)

    assert first != second
    assert first.name.endswith("__s1")
    assert second.name.endswith("__s2")
    assert read_metadata(second)["master_seed"] == 2


def test_run_is_byte_identical_when_called_twice_with_same_seed(tmp_path: Path) -> None:
    run_dir = _run_smoke(tmp_path)
    networks_before = (run_dir / "networks.csv").read_bytes()
    cascades_before = _partition(run_dir).read_bytes()

    run_dir_again = _run_smoke(tmp_path)

    assert run_dir_again == run_dir
    assert (run_dir / "networks.csv").read_bytes() == networks_before
    assert _partition(run_dir).read_bytes() == cascades_before


def test_run_resumes_without_duplicate_network_ids_when_partition_is_missing(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)
    created_at = read_metadata(run_dir)["created_at"]
    _partition(run_dir).unlink()
    metadata = read_metadata(run_dir)
    metadata["status"] = "running"
    write_metadata(run_dir / "metadata.json", metadata)

    _run_smoke(tmp_path)

    frame = read_networks(run_dir / "networks.csv")
    assert frame["network_id"].is_unique
    assert len(frame) == 2
    assert read_metadata(run_dir)["created_at"] == created_at
    assert validate_run(run_dir).cascades == 60


def test_run_resumes_partial_baseline_without_duplicate_rows_when_manifest_is_truncated(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)
    networks_path = run_dir / "networks.csv"
    frame = read_networks(networks_path)
    write_networks(networks_path, [frame.iloc[0].to_dict()])
    metadata = read_metadata(run_dir)
    metadata["status"] = "running"
    write_metadata(run_dir / "metadata.json", metadata)

    _run_smoke(tmp_path)

    resumed = read_networks(networks_path)
    assert resumed["network_id"].tolist() == [1, 2]
    assert validate_run(run_dir).networks == 2


def test_validate_run_rejects_corrupted_cascade_when_bytes_change(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)
    corrupted = tmp_path / "corrupted"
    shutil.copytree(run_dir, corrupted)
    _partition(corrupted).write_bytes(b"not a gzip stream")

    with pytest.raises(ContractError):
        validate_run(corrupted)


def test_validate_run_rejects_isolated_node_when_invariant_is_broken(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)
    networks_path = run_dir / "networks.csv"
    frame = read_networks(networks_path)
    frame.loc[0, "n_isolated"] = 1
    records = frame.astype(object).where(frame.notna(), None).to_dict("records")
    write_networks(networks_path, records)

    metadata = read_metadata(run_dir)
    entry = next(item for item in metadata["files"] if item["path"] == "networks.csv")
    entry["rows"] = count_rows(networks_path)
    entry["sha256"] = sha256_file(networks_path)
    write_metadata(run_dir / "metadata.json", metadata)

    with pytest.raises(ContractError):
        validate_run(run_dir)


def test_run_writes_one_row_per_seed_and_threshold_when_smoke_config(
    tmp_path: Path,
) -> None:
    run_dir = _run_smoke(tmp_path)

    frame = read_cascades(run_dir, "m1_h0.8_p0.4")

    assert len(frame) == 2 * 30 * 1
    assert frame.groupby(["network_id", "seed_id"]).size().eq(1).all()
