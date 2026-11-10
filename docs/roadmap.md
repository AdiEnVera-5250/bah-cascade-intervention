# Roadmap

**Version:** 0.1.0
**Status:** active
**Last updated:** 2026-11-08

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
- `numpy` and `pandas` may be used across the core, storage, runner, and
  analysis layers; `matplotlib` is used for reporting and notebooks;
  `networkx` is used for drawing and test cross-checks.
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
| 1. Deterministic core | completed | Correct networks and cascades | `ruff` and `pytest` green |
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

**Status:** completed.

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

- `storage.py`: deterministic `networks.csv` and cascade gzip writes (`LF`, UTF-8
  without BOM, gzip level 9 with `mtime=0`), readers, and
  `validate_run(run_dir)`. `metadata.json` may contain timestamps and is not
  required to be byte-identical.
- `runner.py`: `run(seed, config, output_dir) -> Path`; controls and interventions
  from a shared `G0`; direct writes to the final run directory with
  `metadata.status` tracking `running`, `completed`, or `failed`; resume by
  `network_id` using `networks.csv` as the manifest; one cascade partition per
  `baseline_id`.
- Integration test with `tmp_path` and a tiny configuration (`N1=20`, `N2=10`).
- `DEMO` configuration: 100 replicates, `m=2`, `N1=250`, `N2=250`, `h1=0.5`,
  `p1=0.2`, and phase-2 arms `(0.0, 0.2)`, the baseline `(0.5, 0.2)`, and
  `(1.0, 0.2)`.
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

**Configuration:** `DEMO`, with 100 replicates, `m=2`, `N1=250`, `N2=250`,
`N=500`, `h1=0.5`, `p1=0.2`, `phi=0.15`, and three phase-2 arms:
`(0.0, 0.2)`, the baseline `(0.5, 0.2)`, and `(1.0, 0.2)`.

**Content:**

1. Derive 100 base seeds and generate 100 independent `G0` graphs from the
   phase-1 parameters.
2. From each `G0`, continue growth into the three phase-2 arms using independent
   intervention seeds.
3. Run one cascade per node at `phi=0.15` on all 300 networks, for 150,000
   cascades in total.
4. Draw a single 1x3 panel with one representative `G0` and its three final
   networks. Each panel uses its own `spring_layout` coordinates with a
   deterministic seed, so the layout is not shared across the arms. Nodes are
   colored by group and sized proportionally to their degree on a shared scale.
   The representative `G0` is the replicate whose baseline mean `S_N` is closest
   to the median baseline mean across the 100 replicates.
5. Draw a slope graph of the per-`G0` mean `S_N` across the three arms, and an
   equivalent slope graph for the median. The arms are ordered by `h2`, so the
   baseline `(0.5, 0.2)` sits in the center, and the vertical axis is logarithmic.
6. Draw a 2x3 grid of 10-bin step histograms of `S_N`, normalized to the fraction
   of cascades per bin, with one column per arm: the top row pools all `G0`
   (50,000 cascades per arm) and the bottom row shows the representative `G0`
   (500 cascades per arm).
7. Show a summary table whose rows are the arms and whose columns are metrics:
   the mean, median, interquartile range, and global cascade fraction of `S_N`,
   plus network topology metrics averaged over the 100 networks of each arm
   (edges, mean and maximum degree, cross-group edge fraction, number of
   components, and largest component size).

The notebook is a descriptive micro-experiment for integration testing. It uses
the public functions directly, does not call the runner, and does not write a run.
It therefore does not require a new value in the `design` field of
`metadata.json`. The 500-node configuration is a demonstration outside the study
design defined in `docs/model.md`; it does not implement the Phase 3 analyses.

**Dependencies:** `jupyter`, `nbclient`, `nbconvert`, and `scipy` are development
dependencies for executing and validating the notebook. They are recorded in
`pyproject.toml` and `uv.lock`.

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
