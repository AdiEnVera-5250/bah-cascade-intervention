# AGENTS.md

## Purpose

This repository contains a research project on how network growth mechanisms and group-level interventions affect cascade dynamics in social networks.

The project combines stochastic network generation with homophily and group-size interventions, threshold-based cascade simulations, Monte Carlo experiments, and statistical analysis of the resulting cascades.

The project must support two first-class capabilities:

1. Generating reproducible datasets from network and cascade simulations.
2. Analyzing those datasets through dedicated analysis workflows.

Data generation and analysis must remain clearly separated, but both are part of the project scope. The project is not limited to producing raw simulation outputs; it must also support the statistical and comparative analyses required by the research questions.

The main comparisons involve:

- Intervened networks versus non-intervened or baseline networks.
- Networks with different homophily regimes.
- Cascades initiated from random seeds and from seeds sampled within specific groups.
- Cascade outcomes across groups, network configurations, and intervention settings.

All experiments must be reproducible from configuration, explicit random seeds, and recorded metadata.

## Scientific Scope

### Network Growth with Homophily

Implement a growing undirected network model with two groups, a minority and a majority.

Core ingredients:

- Preferential attachment.
- A tunable homophily parameter `h` in `[0, 1]`.
- Group sizes controlled by the minority fraction.
- Symmetric homophily by default:
  - `h_aa = h_bb = h`
  - `h_ab = h_ba = 1 - h`
- Asymmetric homophily may be supported only if explicitly requested.
- Attachment probability must depend on node degree and the homophily between node groups.
- The model must support configurable network size, initial seed network, number of links per arriving node, minority fraction, and homophily.

### Two-Phase Network Growth Interventions

Implement a two-phase growth process in which homophily and group sizes may change over time.

Default assumptions:

- Pre-intervention phase: growth under initial homophily and initial minority fraction.
- Post-intervention phase: growth under updated homophily and/or updated minority fraction.
- Phase lengths must remain configurable.
- Interventions may change:
  - Group size: quota or minority fraction in arriving nodes.
  - Behaviour: homophily parameter.
- The implementation must allow comparing:
  - Pre-intervention network.
  - Post-intervention network.
  - Baseline networks generated under pure homophily or other reference conditions.

### Threshold Cascades

Implement a threshold cascade process on an existing undirected network.

Core rule:

- Each node has a threshold `phi_i`.
- A node becomes active if the fraction of its active neighbours is at least its threshold.
- Updates are synchronous by default.
- Isolated nodes must be handled explicitly.
- The initial seed or seeds must be configurable.
- The model must support seeds sampled uniformly at random and seeds sampled from a specified group.

Each cascade simulation must record at least:

- Absolute cascade size.
- Relative cascade size with respect to the whole network.
- Number and fraction of affected nodes by group.
- Whether the cascade is global according to a configurable threshold.
- Stopping time in iterations.
- Initial seed metadata.

### Metrics and Analysis

The project must support both raw per-simulation outputs and aggregated per-network outputs.

Summary statistics should include, where applicable:

- Mean.
- Median.
- Standard deviation.
- Quartiles.
- Global-cascade probability.
- Statistics separated by seed group and overall.

The analysis workflows must be able to consume the generated datasets and produce comparative analyses between networks, interventions, groups, and cascade regimes.

## Development Rules

- Use Python.
- Use `pip`-compatible dependency management.
- Declare dependencies explicitly. Prefer `pyproject.toml`; `requirements.txt` is acceptable if the project is not packaged yet.
- Use a `src/` layout for the Python package.
- Do not use notebooks for the main implementation. Exploratory notebooks may exist, but reusable logic must live in source files.
- Use `snake_case` for modules, files, functions, and variables.
- Use `PascalCase` only for classes when classes are necessary.
- Use `UPPER_SNAKE_CASE` for constants.
- Add type hints to public functions and important internal functions.
- Keep comments to a minimum.
- Functions must be understandable from their names and structure without comments.
- Comments are allowed only for non-obvious mathematical, algorithmic, or reproducibility decisions.
- Avoid large functions. Separate generation, simulation, metric computation, aggregation, and persistence.
- Avoid hardcoded numeric parameters in model or experiment code. Pass them through configuration objects.
- Do not name source files after researchers. Use descriptive domain names that express what the module does.
- Use deterministic random seeds for every stochastic process.
- Never rely on global random state implicitly. Prefer explicit `numpy.random.Generator` instances.
- Use `logging`, not `print`, for experiment progress and diagnostics.
- Do not commit generated datasets, figures, or large output files.
- Do not add new dependencies without explicit approval.
- Do not change scientific assumptions or public interfaces without explicit approval.
- Prefer clear, correct code over premature optimization.
- Use `numpy` for numerical operations, `networkx` for graph manipulation where clarity matters, and `pandas` for tabular outputs.
- Use `pytest` for tests unless the project explicitly adopts another test runner.
- Unit tests must cover model invariants, cascade rules, metric calculations, and aggregation logic.
- Integration tests should use small networks and short simulations.
- Keep experiments reproducible from configuration and seeds.
- Ask before adding dependencies, changing architecture, or altering scientific assumptions.
- Do not invent missing model parameters silently. Make them configurable or ask for clarification.
- Keep changes small and reviewable.

## Architecture

Package under `src/bah_cascade/`, with a strict separation between generation and analysis:

- `config/` — experiment specification as pure Python modules (`DESIGN` + `build_experiment`), validation, design expansion, run snapshot.
- `rng.py` — deterministic stream derivation from a master seed through `numpy.random.SeedSequence` keys.
- `networks/` — initial graph, exact shuffled group quotas, homophilic preferential attachment, paired phase conditions, structural metrics.
- `cascades/` — thresholds, seed sampling, synchronous threshold-cascade engine.
- `experiments/` — Monte Carlo orchestration, persistence, scale benchmark. The only layer allowed to write files.
- `analysis/` — read-only workflows over generated CSV datasets.

Data contracts: `networks.csv`, `cascades.csv`, and an optional `cascade_trajectory.csv`.
`results/` and `reports/` hold generated artifacts and are ignored by git.

Each directory documents its modules, public functions, invariants, and implementation phase in a local `README.md`.
That file is the canonical context source when resuming work.

## Implementation Plan

| Phase | Scope | Status |
|---|---|---|
| 0 | Model specification and ADRs in `docs/` | pending authorization |
| 1 | Skeleton: package, config, rng, CLI, test harness | pending authorization |
| 2 | Network growth: initial graph, quotas, attachment, metrics | pending |
| 3 | Paired two-phase conditions | pending |
| 4 | Cascade engine, thresholds, seeds, scale benchmark | pending |
| 5 | Monte Carlo runner, persistence, resume | pending |
| 6 | Analysis workflows and figures | pending |
| 7 | Calibration runs, example configs, README | pending |

Scaffolding (directories, packaging metadata, per-directory documentation) is complete.
Do not begin a phase without explicit user authorization.