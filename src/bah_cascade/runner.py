"""Experiment runner for the minimum functional pipeline."""

from __future__ import annotations

import os
import platform
import subprocess
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np

from bah_cascade.cascade import simulate_all_seeds
from bah_cascade.config import DesignConfig
from bah_cascade.growth import Network, grow_phase1, grow_phase2
from bah_cascade.metrics import NetworkMetrics, connected_components, network_metrics
from bah_cascade.rng import base_seed, intervention_seed, make_rng
from bah_cascade.storage import (
    MODEL_VERSION,
    SCHEMA_VERSION,
    ContractError,
    append_networks,
    baseline_id,
    count_rows,
    read_metadata,
    read_networks,
    sha256_file,
    write_cascades,
    write_metadata,
)

_GIT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class _NetworkSpec:
    network_id: int
    baseline_id: str
    m: int
    h1: float
    p1: float
    replicate: int
    h2: float
    p2: float
    intervention_type: str
    control_network_id: int | None
    base_seed: int
    intervention_seed: int


def _intervention_type(h1: float, p1: float, h2: float, p2: float) -> str:
    if h2 == h1 and p2 == p1:
        return "none"
    if p2 == p1:
        return "behavioral"
    if h2 == h1:
        return "size"
    return "mixed"


def _build_specs(seed: int, config: DesignConfig) -> tuple[_NetworkSpec, ...]:
    raw: list[tuple[int, float, float, int, float, float]] = []
    for m in config.network.m_values:
        for h1 in config.h_values:
            for p1 in config.p_values:
                targets = sorted({(h1, p1), *config.interventions_for(h1, p1)})
                for replicate in range(1, config.replicates + 1):
                    for h2, p2 in targets:
                        raw.append((m, h1, p1, replicate, h2, p2))
    raw.sort(key=lambda item: (item[0], item[1], item[2], item[3], item[4], item[5]))

    identifiers = {
        (m, h1, p1, replicate, h2, p2): index
        for index, (m, h1, p1, replicate, h2, p2) in enumerate(raw, start=1)
    }
    specs: list[_NetworkSpec] = []
    for m, h1, p1, replicate, h2, p2 in raw:
        control = identifiers[(m, h1, p1, replicate, h1, p1)]
        kind = _intervention_type(h1, p1, h2, p2)
        specs.append(
            _NetworkSpec(
                network_id=identifiers[(m, h1, p1, replicate, h2, p2)],
                baseline_id=baseline_id(m, h1, p1),
                m=m,
                h1=h1,
                p1=p1,
                replicate=replicate,
                h2=h2,
                p2=p2,
                intervention_type=kind,
                control_network_id=None if kind == "none" else control,
                base_seed=base_seed(seed, m, h1, p1, replicate),
                intervention_seed=intervention_seed(seed, m, h1, p1, replicate, h2, p2),
            )
        )
    return tuple(specs)


def _group_by_baseline(
    specs: tuple[_NetworkSpec, ...],
) -> dict[tuple[int, float, float], list[_NetworkSpec]]:
    groups: dict[tuple[int, float, float], list[_NetworkSpec]] = {}
    for spec in specs:
        groups.setdefault((spec.m, spec.h1, spec.p1), []).append(spec)
    return groups


def _network_row(
    spec: _NetworkSpec,
    network: Network,
    metrics: NetworkMetrics,
    n1: int,
    n2: int,
) -> dict[str, Any]:
    return {
        "network_id": spec.network_id,
        "baseline_id": spec.baseline_id,
        "replicate": spec.replicate,
        "intervention_type": spec.intervention_type,
        "control_network_id": spec.control_network_id,
        "h1": spec.h1,
        "p1": spec.p1,
        "h2": spec.h2,
        "p2": spec.p2,
        "m": spec.m,
        "N1": n1,
        "N2": n2,
        "N": network.n_nodes,
        "base_seed": spec.base_seed,
        "intervention_seed": spec.intervention_seed,
        "n_A": metrics.n_A,
        "n_B": metrics.n_B,
        "n_isolated": metrics.n_isolated,
        "n_edges": metrics.n_edges,
        "edges_cross": metrics.edges_cross,
        "edges_within_A": metrics.edges_within_A,
        "edges_within_B": metrics.edges_within_B,
        "n_components": metrics.n_components,
        "largest_component_size": metrics.largest_component_size,
        "k_min": metrics.k_min,
        "k_max": metrics.k_max,
        "k_mean": metrics.k_mean,
        "k_median": metrics.k_median,
        "k_min_A": metrics.k_min_A,
        "k_max_A": metrics.k_max_A,
        "k_mean_A": metrics.k_mean_A,
        "k_median_A": metrics.k_median_A,
        "k_min_B": metrics.k_min_B,
        "k_max_B": metrics.k_max_B,
        "k_mean_B": metrics.k_mean_B,
        "k_median_B": metrics.k_median_B,
        "frac_A": metrics.frac_A,
    }


def _component_sizes(network: Network) -> np.ndarray:
    sizes = np.zeros(network.n_nodes, dtype=np.int64)
    for component in connected_components(network):
        sizes[list(component)] = len(component)
    return sizes


def _cascade_rows(
    spec: _NetworkSpec,
    network: Network,
    phi_values: tuple[float, ...],
    n1: int,
) -> Iterator[dict[str, Any]]:
    n_nodes = network.n_nodes
    degrees = network.degrees()
    groups = network.groups
    component_sizes = _component_sizes(network)
    results = {phi: simulate_all_seeds(network, phi) for phi in phi_values}

    for seed_id in range(n_nodes):
        group = "A" if int(groups[seed_id]) == 0 else "B"
        stage = "base" if seed_id < n1 else "phase2"
        for phi in phi_values:
            result = results[phi][seed_id]
            yield {
                "network_id": spec.network_id,
                "seed_id": seed_id,
                "seed_group": group,
                "seed_degree": int(degrees[seed_id]),
                "seed_stage": stage,
                "seed_component_size": int(component_sizes[seed_id]),
                "phi": phi,
                "S_N": result.S_N,
                "S_A": result.S_A,
                "S_B": result.S_B,
                "S_N_rel": result.S_N / n_nodes,
                "t_s": result.t_s,
                "is_global": result.is_global,
            }


def _baseline_rows(
    config: DesignConfig,
    specs: list[_NetworkSpec],
    networks_path: Path,
    completed: set[int],
) -> Iterator[dict[str, Any]]:
    by_replicate: dict[int, list[_NetworkSpec]] = {}
    for spec in specs:
        by_replicate.setdefault(spec.replicate, []).append(spec)

    for replicate in sorted(by_replicate):
        replicate_specs = by_replicate[replicate]
        first = replicate_specs[0]
        g0 = grow_phase1(
            first.m,
            first.h1,
            first.p1,
            config.network.n1,
            make_rng(first.base_seed),
        )
        for spec in replicate_specs:
            network = grow_phase2(
                g0,
                spec.m,
                spec.h2,
                spec.p2,
                config.network.n2,
                make_rng(spec.intervention_seed),
            )
            metrics = network_metrics(network)
            if spec.network_id not in completed:
                append_networks(
                    networks_path,
                    [_network_row(spec, network, metrics, config.network.n1, config.network.n2)],
                )
                completed.add(spec.network_id)
            yield from _cascade_rows(
                spec,
                network,
                config.cascade.phi_values,
                config.network.n1,
            )


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def _environment() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": _package_version("numpy"),
        "pandas": _package_version("pandas"),
        "networkx": _package_version("networkx"),
        "platform": platform.system(),
    }


def _git_info() -> tuple[str, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_GIT_ROOT,
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=_GIT_ROOT,
                capture_output=True,
                check=True,
                text=True,
            ).stdout.strip()
        )
    except OSError, subprocess.CalledProcessError:
        return "unknown", True
    return commit, dirty


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _run_id(seed: int, config: DesignConfig) -> str:
    return f"{config.name}__{config.config_hash()}__s{seed}"


def _new_metadata(
    seed: int,
    config: DesignConfig,
    run_id: str,
    networks_expected: int,
    cascades_expected: int,
) -> dict[str, Any]:
    git_commit, git_dirty = _git_info()
    return {
        "run_id": run_id,
        "config_name": config.name,
        "config_hash": config.config_hash(),
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "master_seed": seed,
        "status": "running",
        "parameters": config.parameters(),
        "environment": _environment(),
        "files": [],
        "counts": {
            "networks_expected": networks_expected,
            "networks_written": 0,
            "cascades_expected": cascades_expected,
            "cascades_written": 0,
        },
        "duration_seconds": 0.0,
        "notes": "",
    }


def _check_identity(metadata: dict[str, Any], run_id: str, seed: int, config: DesignConfig) -> None:
    if metadata.get("run_id") != run_id:
        raise ContractError("run_id does not match the requested run")
    if metadata.get("config_name") != config.name:
        raise ContractError("config_name does not match the requested configuration")
    if metadata.get("config_hash") != config.config_hash():
        raise ContractError("config_hash does not match the requested configuration")
    if int(metadata.get("master_seed", -1)) != seed:
        raise ContractError("master_seed does not match the requested seed")
    if str(metadata.get("schema_version", "")).split(".")[0] != SCHEMA_VERSION.split(".")[0]:
        raise ContractError("schema_version is not supported")


def _load_or_create(
    seed: int,
    config: DesignConfig,
    run_dir: Path,
    networks_expected: int,
    cascades_expected: int,
) -> dict[str, Any]:
    run_id = run_dir.name
    if run_dir.exists() and (run_dir / "metadata.json").exists():
        metadata = read_metadata(run_dir)
        _check_identity(metadata, run_id, seed, config)
        return metadata
    if not run_dir.exists():
        run_dir.mkdir(parents=True)
    metadata = _new_metadata(seed, config, run_id, networks_expected, cascades_expected)
    write_metadata(run_dir / "metadata.json", metadata)
    return metadata


def _repair_incomplete_line(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    with path.open("rb+") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(-1, os.SEEK_END)
        if handle.read(1) == b"\n":
            return
        position = size
        while position > 0:
            start = max(0, position - 8192)
            handle.seek(start)
            chunk = handle.read(position - start)
            newline = chunk.rfind(b"\n")
            if newline != -1:
                handle.truncate(start + newline + 1)
                return
            position = start
        handle.truncate(0)


def _completed_ids(networks_path: Path) -> set[int]:
    if not networks_path.exists() or networks_path.stat().st_size == 0:
        return set()
    _repair_incomplete_line(networks_path)
    frame = read_networks(networks_path)
    return {int(value) for value in frame["network_id"].tolist()}


def _file_entry(run_dir: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": path.relative_to(run_dir).as_posix(),
        "format": "csv",
        "compression": "gzip" if path.suffix == ".gz" else "none",
        "rows": rows,
        "sha256": sha256_file(path),
    }


def _ordered_entries(entries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        entries[path] for path in sorted(entries, key=lambda item: (item != "networks.csv", item))
    ]


def run(seed: int, config: DesignConfig, output_dir: str | Path) -> Path:
    """Execute a configured run and return its directory.

    The runner writes directly to ``<output_dir>/<run_id>`` and uses
    ``metadata.status`` to mark running, completed, or failed executions.
    ``networks.csv`` is the resume manifest.
    """
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = _build_specs(seed, config)
    networks_expected = len(specs)
    n_nodes = config.network.n1 + config.network.n2
    n_phi = len(config.cascade.phi_values)
    cascades_expected = networks_expected * n_nodes * n_phi
    run_dir = output_dir / _run_id(seed, config)

    metadata = _load_or_create(
        seed,
        config,
        run_dir,
        networks_expected,
        cascades_expected,
    )
    if metadata.get("status") == "completed":
        return run_dir

    metadata["status"] = "running"
    write_metadata(run_dir / "metadata.json", metadata)

    started = time.monotonic()
    previous_duration = float(metadata.get("duration_seconds", 0.0))
    networks_path = run_dir / "networks.csv"
    completed = _completed_ids(networks_path)
    entries: dict[str, dict[str, Any]] = {
        str(entry["path"]): dict(entry)
        for entry in metadata.get("files", [])
        if isinstance(entry, dict) and "path" in entry
    }
    partition_rows: dict[str, int] = {}

    try:
        for (m, h1, p1), baseline_specs in _group_by_baseline(specs).items():
            baseline = baseline_id(m, h1, p1)
            partition = run_dir / "cascades" / f"{baseline}.csv.gz"
            relative = partition.relative_to(run_dir).as_posix()
            all_completed = all(spec.network_id in completed for spec in baseline_specs)

            if all_completed and partition.exists():
                if relative in entries:
                    partition_rows[relative] = int(entries[relative]["rows"])
                else:
                    partition_rows[relative] = count_rows(partition)
                    entries[relative] = _file_entry(run_dir, partition, partition_rows[relative])
            else:
                if partition.exists():
                    partition.unlink()
                rows = write_cascades(
                    partition,
                    _baseline_rows(config, baseline_specs, networks_path, completed),
                )
                partition_rows[relative] = rows
                entries[relative] = _file_entry(run_dir, partition, rows)

            metadata["counts"]["networks_written"] = len(completed)
            metadata["counts"]["cascades_written"] = sum(partition_rows.values())
            metadata["files"] = _ordered_entries(entries)
            write_metadata(run_dir / "metadata.json", metadata)

        if len(completed) != networks_expected:
            raise ContractError("not every network was written")
        entries["networks.csv"] = _file_entry(
            run_dir,
            networks_path,
            len(completed),
        )
        metadata["files"] = _ordered_entries(entries)
        metadata["counts"]["networks_written"] = len(completed)
        metadata["counts"]["cascades_written"] = sum(partition_rows.values())
        metadata["duration_seconds"] = previous_duration + (time.monotonic() - started)
        metadata["status"] = "completed"
        write_metadata(run_dir / "metadata.json", metadata)
    except BaseException:
        metadata["status"] = "failed"
        metadata["duration_seconds"] = previous_duration + (time.monotonic() - started)
        metadata["counts"]["networks_written"] = len(completed)
        metadata["counts"]["cascades_written"] = sum(partition_rows.values())
        metadata["files"] = _ordered_entries(entries)
        write_metadata(run_dir / "metadata.json", metadata)
        raise

    return run_dir
