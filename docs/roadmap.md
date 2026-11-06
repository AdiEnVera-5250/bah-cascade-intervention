# Roadmap

**Version:** 0.1.0
**Status:** active
**Last updated:** 2026-11-06

This document tracks phases, deliverables, and exit criteria. Scientific decisions
live in `docs/model.md`, Section 8. Artifact details live in
`docs/data-contracts.md`.

## 1. Principles

- Flat package `src/bah_cascade/`: no subpackages, no per-directory READMEs.
- Functions and frozen dataclasses. No class hierarchies, plugin systems, or
  service layers.
- Python API only. There is no command-line interface and no `__main__.py`.
  Execution happens from scripts or notebooks.
- `config.py` holds named, immutable configurations. No external config parser.
- `numpy` in the core; `pandas` and `matplotlib` in analysis and reporting;
  `networkx` for drawing and test cross-checks.
- Current dependencies are kept. New dependencies require explicit approval.
- The runner is the only writer of `results/`; analysis writes only to `reports/`.
- One commit per phase, Conventional Commits, one topic per commit.

## 2. Target layout

```
bah-cascade-intervention/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── docs/
│   ├── model.md
│   ├── data-contracts.md
│   └── roadmap.md
├── notebooks/
│   └── demo.ipynb
├── src/bah_cascade/
│   ├── __init__.py
│   ├── config.py
│   ├── rng.py
│   ├── growth.py
│   ├── cascade.py
│   ├── metrics.py
│   ├── storage.py
│   └── runner.py
├── tests/
│   ├── test_config.py
│   ├── test_growth.py
│   ├── test_cascade.py
│   ├── test_metrics.py
│   ├── test_storage.py
│   └── test_runner.py
├── results/.gitignore
└── reports/.gitignore
```

`analysis.py` and `notebooks/analysis.ipynb` are added in Phase 3. `notebooks/` is
a new top-level directory approved by this plan. The notebooks are committed
without execution outputs.

## 3. Phases

| Phase | Status | Goal | Exit criterion |
|---|---|---|---|
| 0. Repository baseline | completed | Coherent repo, no stale artifacts | `uv sync` works; clean tree |
| 1. Deterministic core | pending | Correct networks and cascades | `ruff` and `pytest` green |
| 2. Minimum functional pipeline | pending | Contract-valid run plus demo notebook | Smoke run validates; notebook runs |
| 3. Descriptive analysis | pending | Answer the study questions | Reports generated from a validated run |
| 4. Scale and final run | pending | Make 187.5M cascades viable | Throughput measured; `R` fixed; run complete |

### Phase 0 — Repository baseline

**Status:** completed.

Tasks:

- [x] Delete stale artifacts from the previous architecture:
  `results/calibration__*/`, `results/calibration_*.log`, and
  `results/benchmark.csv`.
- [x] Create `src/bah_cascade/__init__.py` so the declared package builds.
- [x] Update `AGENTS.md`: remove `docs/decisions/` from the source-of-truth list
  and renumber the remaining entries.
- [x] Update `README.md`: replace the planned ADR line with a reference to
  `docs/roadmap.md`.
- [x] Write this roadmap.
- [x] Commit the current documentation set: `model.md`, `data-contracts.md`,
  `roadmap.md`, and the cleaned tree.

Exit criteria:

- `uv sync` completes.
- `git status` is clean after the commit.
- No generated artifacts remain outside the ignored directories.

### Phase 1 — Deterministic core

**Status:** pending.

Tasks:

- `config.py`: frozen dataclasses for network, cascade, and design parameters;
  named configurations `SMOKE`, `DEMO`, and `PILOT`; validation; canonical JSON
  hash.
- `rng.py`: `SeedSequence` derivation with explicit keys per stream.
- `growth.py`: three seed-graph regimes, degree bag, homophily rejection, two-phase
  growth.
- `cascade.py`: synchronous threshold rule, exhaustive seeds, `S_N`, `S_A`, `S_B`,
  `t_s`, `is_global`.
- `metrics.py`: degrees, medians, components, cross and within edge counts.
- Unit tests with hand-computed values: `m=1`, `m0=4`, `h1=0` gives `K_{2,2}`;
  `h1=1` gives two `K_2`; intermediate `h1` gives `K_4`.

Exit criteria:

- Every node has degree at least `m`.
- No self-loops and no multiple edges.
- Bag multiplicity equals degree at every step.
- The same seed reproduces the same network exactly.
- A hand-built cascade reproduces the expected `S_N` and `t_s`.
- `uv run ruff check .`, `uv run ruff format --check .`, and `uv run pytest` pass.

### Phase 2 — Minimum functional pipeline

**Status:** pending.

Tasks:

- `storage.py`: deterministic CSV and gzip writes (`LF`, UTF-8 without BOM, gzip
  level 9 with `mtime=0`), readers, and `validate_run(run_dir)`.
- `runner.py`: `run(config, output_dir) -> Path`; controls and interventions from
  a shared `G0`; resume by `network_id`; one cascade partition per `baseline_id`.
- Integration test with `tmp_path` and a tiny configuration (`N1=20`, `N2=10`).
- `DEMO` configuration: `m=1`, `N1=50`, `N2=50`, `h1=0.8`, `p1=0.4`, `h2=0.2`,
  `p2=0.4`.
- `notebooks/demo.ipynb`.

Exit criteria:

- A smoke run writes `metadata.json`, `networks.csv`, and
  `cascades/*.csv.gz`.
- `validate_run` accepts the smoke run and rejects a corrupted copy.
- The notebook runs end to end and its outputs are cleared before commit.
- `ruff` and `pytest` pass.

**The minimum functional milestone is reached at the end of this phase.**

### Phase 2 notebook

**File:** `notebooks/demo.ipynb`.

**Configuration:** `DEMO`, with `m=1`, `N1=50`, `N2=50`, `N=100`, `h1=0.8`,
`p1=0.4`, `h2=0.2`, `p2=0.4`, and `phi=0.15`.

**Content:**

1. Build `G0` once from the phase-1 parameters.
2. Continue growth twice from the same `G0`: the control with `(h1, p1)` and the
   intervened network with `(h2, p2)`.
3. Draw both graphs side by side, with nodes colored by group and a fixed layout
   seed.
4. Run 100 cascades per network, one per node, at `phi=0.15`; 200 cascades in
   total.
5. Show a 2x2 histogram grid: `S_N` and `t_s`, with control and intervened
   networks side by side, using a fixed bin count.
6. Print mean, median, and global-cascade fraction for both networks.

The notebook uses the public functions directly and does not write a run. It
therefore does not require a new value in the `design` field of `metadata.json`.
The 100-node configuration is a demonstration outside the study design defined in
`docs/model.md`.

### Phase 3 — Descriptive analysis

**Status:** pending.

Tasks:

- `analysis.py`: load and validate a run; seed-level summaries; paired differences
  `Delta S_N`; heatmaps; `phi*`; Watts `rho`; seed classes; clustering.
- `notebooks/analysis.ipynb`: run the six analyses over a validated run and write
  figures and tables to `reports/<run_id>/`.
- `docs/analysis-contracts.md` only if derived tables are persisted.

Exit criteria:

- The six analyses run on a validated run.
- Outputs go only to `reports/`.
- No generated artifacts are committed.

### Phase 4 — Scale and final run

**Status:** pending.

Tasks:

- Benchmark the cascade kernel on an `N=500` network: 500 seeds and 4 thresholds.
- Extrapolate to 187.5M cascades and choose the execution strategy: current
  kernel, vectorized `numpy`, or a compiled kernel. A compiled kernel requires
  dependency approval.
- Add process-level parallelism if needed.
- Run the power analysis at the level of `G0` to fix `R`.
- Execute the final design and record checksums and wall-clock time.

Exit criteria:

- Measured throughput and estimated wall-clock time are documented.
- The final `R` is justified.
- The full run validates against `docs/data-contracts.md`.
- Artifacts remain outside git.

## 4. Feasibility gate

The full design is 187.5 million cascades. Before optimizing, Phase 4 measures the
real throughput of the Phase 2 kernel. The decision tree is:

1. If the full run fits the available time, keep the simple kernel.
2. If not, reduce `R` first; the model already treats `R` as provisional.
3. If more speed is still required, parallelize by network or baseline.
4. Only then consider a compiled kernel, with explicit dependency approval.

## 5. Out of scope

- Command-line interface.
- `docs/decisions/` as a separate ADR directory.
- Cascade trajectories.
- Heterogeneous thresholds and mixed robustness subsets beyond the main grid.
- Formal inference.

## 6. Change control

Phases start only with explicit authorization. Changes to `docs/model.md`,
`docs/data-contracts.md`, or the RNG module require approval. No new dependencies
without approval. Phase status is updated in this document at the end of each
phase.
