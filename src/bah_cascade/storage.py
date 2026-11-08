"""Deterministic run serialization and data-contract validation."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import tempfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCHEMA_VERSION = "2.0"
MODEL_VERSION = "0.4.0"

NETWORK_COLUMNS: tuple[str, ...] = (
    "network_id",
    "baseline_id",
    "replicate",
    "intervention_type",
    "control_network_id",
    "h1",
    "p1",
    "h2",
    "p2",
    "m",
    "N1",
    "N2",
    "N",
    "base_seed",
    "intervention_seed",
    "n_A",
    "n_B",
    "n_isolated",
    "n_edges",
    "edges_cross",
    "edges_within_A",
    "edges_within_B",
    "n_components",
    "largest_component_size",
    "k_min",
    "k_max",
    "k_mean",
    "k_median",
    "k_min_A",
    "k_max_A",
    "k_mean_A",
    "k_median_A",
    "k_min_B",
    "k_max_B",
    "k_mean_B",
    "k_median_B",
    "frac_A",
)

CASCADE_COLUMNS: tuple[str, ...] = (
    "network_id",
    "seed_id",
    "seed_group",
    "seed_degree",
    "seed_stage",
    "seed_component_size",
    "phi",
    "S_N",
    "S_A",
    "S_B",
    "S_N_rel",
    "t_s",
    "is_global",
)

_NETWORK_DTYPES: dict[str, str] = {
    "network_id": "int64",
    "baseline_id": "string",
    "replicate": "int64",
    "intervention_type": "string",
    "control_network_id": "Int64",
    "h1": "float64",
    "p1": "float64",
    "h2": "float64",
    "p2": "float64",
    "m": "int64",
    "N1": "int64",
    "N2": "int64",
    "N": "int64",
    "base_seed": "uint64",
    "intervention_seed": "uint64",
    "n_A": "int64",
    "n_B": "int64",
    "n_isolated": "int64",
    "n_edges": "int64",
    "edges_cross": "int64",
    "edges_within_A": "int64",
    "edges_within_B": "int64",
    "n_components": "int64",
    "largest_component_size": "int64",
    "k_min": "int64",
    "k_max": "int64",
    "k_mean": "float64",
    "k_median": "float64",
    "k_min_A": "int64",
    "k_max_A": "int64",
    "k_mean_A": "float64",
    "k_median_A": "float64",
    "k_min_B": "int64",
    "k_max_B": "int64",
    "k_mean_B": "float64",
    "k_median_B": "float64",
    "frac_A": "float64",
}

_CASCADE_DTYPES: dict[str, str] = {
    "network_id": "int64",
    "seed_id": "int64",
    "seed_group": "string",
    "seed_degree": "int64",
    "seed_stage": "string",
    "seed_component_size": "int64",
    "phi": "float64",
    "S_N": "int64",
    "S_A": "int64",
    "S_B": "int64",
    "S_N_rel": "float64",
    "t_s": "int64",
    "is_global": "int64",
}


class ContractError(ValueError):
    """Raised when a run violates ``docs/data-contracts.md``."""


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Counts produced by a successful validation."""

    networks: int
    cascades: int


def _format_float(value: float) -> str:
    return repr(float(value))


def baseline_id(m: int, h1: float, p1: float) -> str:
    """Return the baseline identifier for ``(m, h1, p1)``."""
    return f"m{m}_h{_format_float(h1)}_p{_format_float(p1)}"


def _format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("CSV values must be finite")
        return repr(number)
    return str(value)


def _temporary_path(path: Path) -> Path:
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    os.close(descriptor)
    return Path(name)


def _write_rows(
    writer: Any,
    columns: tuple[str, ...],
    rows: Iterable[Mapping[str, object]],
    key: Callable[[Mapping[str, object]], tuple[object, ...]],
) -> int:
    previous: tuple[object, ...] | None = None
    count = 0
    for row in rows:
        current = key(row)
        if previous is not None and current <= previous:
            raise ValueError("rows must be sorted by primary key")
        writer.writerow([_format_value(row[column]) for column in columns])
        previous = current
        count += 1
    return count


def _write_plain_csv(
    path: Path,
    columns: tuple[str, ...],
    rows: Iterable[Mapping[str, object]],
    key: Callable[[Mapping[str, object]], tuple[object, ...]],
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(path)
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(columns)
            count = _write_rows(writer, columns, rows, key)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return count


def _write_gzip_csv(
    path: Path,
    columns: tuple[str, ...],
    rows: Iterable[Mapping[str, object]],
    key: Callable[[Mapping[str, object]], tuple[object, ...]],
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(path)
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw,
                compresslevel=9,
                mtime=0,
            ) as compressed:
                text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
                try:
                    writer = csv.writer(text, lineterminator="\n")
                    writer.writerow(columns)
                    count = _write_rows(writer, columns, rows, key)
                    text.flush()
                finally:
                    text.detach()
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return count


def write_metadata(path: Path, metadata: Mapping[str, object]) -> None:
    """Write ``metadata.json`` deterministically, except for its timestamps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        metadata,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    temporary = _temporary_path(path)
    try:
        temporary.write_bytes(payload.encode("utf-8") + b"\n")
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def read_metadata(run_dir: Path) -> dict[str, Any]:
    """Read ``metadata.json`` from a run directory."""
    path = run_dir / "metadata.json"
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("metadata.json must contain a JSON object")
    return value


def write_networks(path: Path, rows: Iterable[Mapping[str, object]]) -> int:
    """Write ``networks.csv`` atomically and return the number of rows."""
    return _write_plain_csv(
        path,
        NETWORK_COLUMNS,
        rows,
        key=lambda row: (int(row["network_id"]),),
    )


def append_networks(path: Path, rows: Iterable[Mapping[str, object]]) -> int:
    """Append completed network rows to the resume manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path.exists() or path.stat().st_size == 0
    count = 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if needs_header:
            writer.writerow(NETWORK_COLUMNS)
        for row in rows:
            writer.writerow([_format_value(row[column]) for column in NETWORK_COLUMNS])
            count += 1
    return count


def write_cascades(path: Path, rows: Iterable[Mapping[str, object]]) -> int:
    """Write a deterministic gzip cascade partition and return its row count."""
    return _write_gzip_csv(
        path,
        CASCADE_COLUMNS,
        rows,
        key=lambda row: (
            int(row["network_id"]),
            int(row["seed_id"]),
            float(row["phi"]),
        ),
    )


def _read_csv(path: Path, dtypes: Mapping[str, str]) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=dict(dtypes))
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise ContractError(f"cannot read {path}: {exc}") from exc


def read_networks(path: Path) -> pd.DataFrame:
    """Read ``networks.csv`` with contract column types."""
    return _read_csv(path, _NETWORK_DTYPES)


def read_cascades(run_dir: Path, baseline: str) -> pd.DataFrame:
    """Read one cascade partition for ``baseline``."""
    compressed = run_dir / "cascades" / f"{baseline}.csv.gz"
    parquet = run_dir / "cascades" / f"{baseline}.parquet"
    if compressed.exists():
        return _read_csv(compressed, _CASCADE_DTYPES)
    if parquet.exists():
        try:
            return pd.read_parquet(parquet)
        except (OSError, ValueError, ImportError) as exc:
            raise ContractError(f"cannot read {parquet}: {exc}") from exc
    raise ContractError(f"missing cascade partition for {baseline}")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_rows(path: Path) -> int:
    """Count data rows in a plain or gzip CSV file, excluding the header."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _check_columns(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    _require(list(frame.columns) == list(columns), f"{name} has an invalid column order")


def _close(left: pd.Series, right: pd.Series) -> bool:
    return bool(np.allclose(left.to_numpy(), right.to_numpy(), rtol=0.0, atol=1e-12))


def _validate_network_values(frame: pd.DataFrame, metadata: Mapping[str, Any]) -> None:
    parameters = metadata["parameters"]
    n_nodes = frame["N"]

    _require((frame["n_A"] > 0).all(), "n_A must be positive")
    _require((frame["n_B"] > 0).all(), "n_B must be positive")
    _require((frame["n_A"] + frame["n_B"] == n_nodes).all(), "n_A + n_B must equal N")
    _require((frame["n_isolated"] == 0).all(), "isolated nodes are not allowed")
    _require(
        (
            frame["n_edges"]
            == frame["edges_cross"] + frame["edges_within_A"] + frame["edges_within_B"]
        ).all(),
        "n_edges must equal the sum of edge classes",
    )
    _require(
        _close(frame["k_mean"], 2.0 * frame["n_edges"] / n_nodes),
        "k_mean must equal 2 * n_edges / N",
    )
    _require(
        _close(
            frame["k_mean_A"],
            (2.0 * frame["edges_within_A"] + frame["edges_cross"]) / frame["n_A"],
        ),
        "k_mean_A is inconsistent with edge counts",
    )
    _require(
        _close(
            frame["k_mean_B"],
            (2.0 * frame["edges_within_B"] + frame["edges_cross"]) / frame["n_B"],
        ),
        "k_mean_B is inconsistent with edge counts",
    )
    _require((frame["n_components"] >= 1).all(), "n_components must be positive")
    _require(
        (
            (frame["largest_component_size"] >= 1) & (frame["largest_component_size"] <= n_nodes)
        ).all(),
        "largest_component_size is outside the network",
    )
    _require((frame["k_min"] >= frame["m"]).all(), "k_min must be at least m")
    _require((frame["k_min_A"] >= frame["m"]).all(), "k_min_A must be at least m")
    _require((frame["k_min_B"] >= frame["m"]).all(), "k_min_B must be at least m")
    _require(
        (frame["k_min"] == np.minimum(frame["k_min_A"], frame["k_min_B"])).all(),
        "k_min must equal min(k_min_A, k_min_B)",
    )
    _require(
        (frame["k_max"] == np.maximum(frame["k_max_A"], frame["k_max_B"])).all(),
        "k_max must equal max(k_max_A, k_max_B)",
    )
    for prefix in ("", "_A", "_B"):
        _require(
            (
                (frame[f"k_min{prefix}"] <= frame[f"k_median{prefix}"])
                & (frame[f"k_median{prefix}"] <= frame[f"k_max{prefix}"])
            ).all(),
            f"k_median{prefix} must lie between the minimum and maximum",
        )
    _require(_close(frame["frac_A"], frame["n_A"] / n_nodes), "frac_A must equal n_A / N")

    for name in ("h1", "p1", "h2", "p2"):
        _require(frame[name].between(0.0, 1.0).all(), f"{name} must lie in [0, 1]")

    _require(
        (
            frame["m"].isin(parameters["M"])
            & (frame["N1"] == parameters["N1"])
            & (frame["N2"] == parameters["N2"])
            & (frame["N"] == parameters["N"])
        ).all(),
        "network sizes or m do not match metadata parameters",
    )


def _validate_intervention_types(frame: pd.DataFrame) -> None:
    none = frame["intervention_type"].eq("none")
    behavioral = frame["intervention_type"].eq("behavioral")
    size = frame["intervention_type"].eq("size")
    mixed = frame["intervention_type"].eq("mixed")
    _require((none | behavioral | size | mixed).all(), "unknown intervention_type")

    _require(
        (frame.loc[none, "h2"] == frame.loc[none, "h1"]).all()
        and (frame.loc[none, "p2"] == frame.loc[none, "p1"]).all(),
        "controls must use the phase-1 parameters",
    )
    _require(
        (frame.loc[behavioral, "h2"] != frame.loc[behavioral, "h1"]).all()
        and (frame.loc[behavioral, "p2"] == frame.loc[behavioral, "p1"]).all(),
        "behavioral interventions must change only h",
    )
    _require(
        (frame.loc[size, "h2"] == frame.loc[size, "h1"]).all()
        and (frame.loc[size, "p2"] != frame.loc[size, "p1"]).all(),
        "size interventions must change only p",
    )
    _require(
        (frame.loc[mixed, "h2"] != frame.loc[mixed, "h1"]).all()
        and (frame.loc[mixed, "p2"] != frame.loc[mixed, "p1"]).all(),
        "mixed interventions must change h and p",
    )

    _require(frame.loc[none, "control_network_id"].isna().all(), "controls cannot have a FK")
    _require(
        frame.loc[~none, "control_network_id"].notna().all(),
        "interventions require control_network_id",
    )


def _validate_controls(frame: pd.DataFrame) -> None:
    controls = frame.loc[frame["intervention_type"] == "none"].set_index("network_id")
    for row in frame.loc[frame["intervention_type"] != "none"].itertuples(index=False):
        control_id = int(row.control_network_id)
        _require(control_id in controls.index, f"control {control_id} does not exist")
        control = controls.loc[control_id]
        _require(control["intervention_type"] == "none", f"network {control_id} is not a control")
        for column in ("baseline_id", "replicate", "base_seed", "h1", "p1", "m"):
            _require(
                row._asdict()[column] == control[column],
                f"control {control_id} does not share {column}",
            )


def _validate_network_keys(frame: pd.DataFrame, metadata: Mapping[str, Any]) -> None:
    _require(frame["network_id"].is_unique, "network_id must be unique")
    _require(frame["network_id"].is_monotonic_increasing, "rows are not sorted by network_id")
    _require(
        not frame.duplicated(["baseline_id", "replicate", "h2", "p2"]).any(),
        "(baseline_id, replicate, h2, p2) must be unique",
    )
    _require(
        not frame.groupby(["baseline_id", "replicate"])["base_seed"].nunique().gt(1).any(),
        "base_seed must be constant within a base graph",
    )

    parameters = metadata["parameters"]
    _require(
        frame["baseline_id"].nunique() == parameters["baselines"],
        "baseline count does not match metadata",
    )
    expected = [
        baseline_id(int(row.m), float(row.h1), float(row.p1))
        for row in frame[["m", "h1", "p1"]].itertuples(index=False)
    ]
    _require(
        (frame["baseline_id"].astype(str).to_numpy() == np.asarray(expected)).all(),
        "baseline_id does not match (m, h1, p1)",
    )

    targets = frame.loc[frame["intervention_type"] != "none"]
    counts = targets.groupby(["baseline_id", "replicate"]).size()
    _require(
        (counts == parameters["interventions_per_baseline"]).all(),
        "intervention count does not match metadata",
    )
    per_replicate = frame.groupby(["baseline_id", "replicate"]).size()
    _require(
        (per_replicate == parameters["interventions_per_baseline"] + 1).all(),
        "every base graph must have one control and K interventions",
    )
    expected_networks = (
        parameters["baselines"] * (parameters["interventions_per_baseline"] + 1) * parameters["R"]
    )
    _require(len(frame) == expected_networks, "network row count does not match parameters")
    _require(
        metadata["counts"]["networks_expected"] == expected_networks,
        "networks_expected does not match parameters",
    )
    _require(
        metadata["counts"]["networks_written"] == len(frame),
        "networks_written does not match networks.csv",
    )


def _validate_cascades(
    run_dir: Path,
    networks: pd.DataFrame,
    metadata: Mapping[str, Any],
) -> int:
    _require(
        metadata.get("status") == "completed",
        "validate_run requires metadata.status = completed",
    )
    parameters = metadata["parameters"]
    phi_values = np.asarray(sorted(float(value) for value in parameters["Phi"]), dtype=np.float64)
    n_phi = int(phi_values.size)
    total = 0
    network_info = networks.set_index("network_id")[["baseline_id", "m", "N1", "N"]]

    for baseline in networks["baseline_id"].drop_duplicates().tolist():
        frame = read_cascades(run_dir, baseline)
        _check_columns(frame, CASCADE_COLUMNS, f"cascades/{baseline}")
        group = networks.loc[networks["baseline_id"] == baseline]
        _require(
            len(frame) == len(group) * int(parameters["N"]) * n_phi,
            f"cascade row count is wrong for {baseline}",
        )
        _require(
            frame["network_id"].isin(group["network_id"]).all(),
            f"cascade partition {baseline} references a foreign network",
        )

        ids = frame["network_id"].to_numpy()
        seeds = frame["seed_id"].to_numpy()
        phis = frame["phi"].to_numpy()
        ordered = (ids[1:] > ids[:-1]) | (
            (ids[1:] == ids[:-1])
            & ((seeds[1:] > seeds[:-1]) | ((seeds[1:] == seeds[:-1]) & (phis[1:] > phis[:-1])))
        )
        _require(bool(ordered.all()), f"cascade partition {baseline} is not sorted")
        _require(
            frame.groupby(["network_id", "seed_id"]).size().eq(n_phi).all(),
            f"cascade partition {baseline} does not have one row per threshold",
        )
        _require(
            frame["phi"].isin(phi_values).all(),
            f"cascade partition {baseline} uses an unknown threshold",
        )

        n_nodes = frame["network_id"].map(network_info["N"]).astype("int64")
        n1 = frame["network_id"].map(network_info["N1"]).astype("int64")
        m = frame["network_id"].map(network_info["m"]).astype("int64")
        _require(
            ((frame["seed_id"] >= 0) & (frame["seed_id"] < n_nodes)).all(), "seed out of range"
        )
        _require((frame["seed_degree"] >= m).all(), "seed_degree must be at least m")
        _require(frame["seed_group"].isin(["A", "B"]).all(), "unknown seed_group")
        _require(
            (frame["seed_stage"] == np.where(frame["seed_id"] < n1, "base", "phase2")).all(),
            "seed_stage is inconsistent with seed_id",
        )
        _require((frame["S_N"] >= 1).all(), "S_N must be at least one")
        _require((frame["S_N"] <= n_nodes).all(), "S_N exceeds the network size")
        _require((frame["S_N"] == frame["S_A"] + frame["S_B"]).all(), "S_N must equal S_A + S_B")
        _require(
            ((frame["seed_group"] != "A") | (frame["S_A"] >= 1)).all(),
            "an A seed must activate at least one A node",
        )
        _require(
            ((frame["seed_group"] != "B") | (frame["S_B"] >= 1)).all(),
            "a B seed must activate at least one B node",
        )
        _require(
            (
                (frame["S_N"] <= frame["seed_component_size"])
                & (frame["seed_component_size"] <= n_nodes)
            ).all(),
            "S_N must fit inside the seed component",
        )
        _require(_close(frame["S_N_rel"], frame["S_N"] / n_nodes), "S_N_rel must equal S_N / N")
        _require((frame["t_s"] >= 0).all(), "t_s must be non-negative")
        expected_global = (2 * frame["S_N"] > n_nodes).astype("int64")
        _require((frame["is_global"] == expected_global).all(), "is_global is inconsistent")
        total += len(frame)

    _require(
        metadata["counts"]["cascades_expected"] == len(networks) * int(parameters["N"]) * n_phi,
        "cascades_expected does not match parameters",
    )
    _require(
        metadata["counts"]["cascades_written"] == total,
        "cascades_written does not match the partitions",
    )
    return total


def _validate_files(run_dir: Path, metadata: Mapping[str, Any], baselines: list[str]) -> None:
    entries = metadata.get("files")
    _require(isinstance(entries, list) and entries, "metadata.files must be a non-empty list")
    paths: list[str] = []
    for entry in entries:
        _require(isinstance(entry, dict), "each metadata.files entry must be an object")
        path = str(entry.get("path", ""))
        _require(path and not path.startswith("/") and ".." not in Path(path).parts, "invalid path")
        paths.append(path)
        file_path = run_dir / path
        _require(file_path.exists(), f"missing artifact {path}")
        try:
            rows = count_rows(file_path)
            digest = sha256_file(file_path)
        except OSError as exc:
            raise ContractError(f"cannot read artifact {path}: {exc}") from exc
        _require(int(entry["rows"]) == rows, f"row count mismatch for {path}")
        _require(str(entry["sha256"]) == digest, f"hash mismatch for {path}")
        if path.endswith(".csv.gz"):
            _require(entry.get("format") == "csv", f"wrong format for {path}")
            _require(entry.get("compression") == "gzip", f"wrong compression for {path}")
        elif path.endswith(".csv"):
            _require(entry.get("format") == "csv", f"wrong format for {path}")
            _require(entry.get("compression") == "none", f"wrong compression for {path}")

    _require(len(paths) == len(set(paths)), "metadata.files contains duplicates")
    _require("networks.csv" in paths, "metadata.files must list networks.csv")
    for baseline in baselines:
        matches = [path for path in paths if path.startswith(f"cascades/{baseline}.")]
        _require(len(matches) == 1, f"metadata.files must list one partition for {baseline}")


def validate_run(run_dir: Path) -> ValidationReport:
    """Validate every artifact in ``run_dir`` against the data contract."""
    run_dir = Path(run_dir)
    metadata = read_metadata(run_dir)
    _require(metadata.get("run_id") == run_dir.name, "run_id must equal the directory name")
    _require(
        str(metadata.get("schema_version", "")).split(".")[0] == SCHEMA_VERSION.split(".")[0],
        "unsupported schema_version",
    )
    _require(metadata.get("status") == "completed", "run status must be completed")
    _require(isinstance(metadata.get("parameters"), dict), "metadata.parameters is missing")
    _require(isinstance(metadata.get("counts"), dict), "metadata.counts is missing")

    networks = read_networks(run_dir / "networks.csv")
    _check_columns(networks, NETWORK_COLUMNS, "networks.csv")
    _require(not networks.empty, "networks.csv must not be empty")
    _validate_network_keys(networks, metadata)
    _validate_network_values(networks, metadata)
    _validate_intervention_types(networks)
    _validate_controls(networks)

    baselines = networks["baseline_id"].astype(str).drop_duplicates().tolist()
    _validate_files(run_dir, metadata, baselines)
    cascades = _validate_cascades(run_dir, networks, metadata)
    return ValidationReport(networks=len(networks), cascades=cascades)
