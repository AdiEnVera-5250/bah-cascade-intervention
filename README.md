# bah-cascade-intervention

Research project on how network growth mechanisms and group-level interventions
affect cascade dynamics in social networks.

The project combines stochastic network generation with homophily and group-size
interventions, threshold cascade simulations, Monte Carlo experiments, and
statistical analysis of the resulting cascades.

## Status

The deterministic core is implemented: network growth with homophily, the
two-phase growth intervention, the threshold cascade engine, and the network and
cascade metrics. The storage and runner layers of the minimum functional pipeline
are in place, and `notebooks/demo.ipynb` exercises the whole path, from 100 base
graphs to 250,000 cascades over five phase-2 arms.

The descriptive analysis and the scaled final run are still pending. Phase status
and exit criteria are tracked in `docs/roadmap.md`.

- `docs/model.md` — network growth, cascade model, experimental design, metrics,
  and analysis plan.
- `docs/data-contracts.md` — files, columns, keys, invariants, and serialization.

**Next steps (under consideration, not yet decided).** The executed demo notebook
suggests that per-network means and medians of `S_N` are not fully representative
of the seed-level cascade distribution, so the Phase 3 analysis plan in
`docs/model.md`, Section 7, is being re-evaluated: some analyses may be dropped
and others added before implementation. In parallel, the cascade engine is being
reviewed for performance, since it is the main computational bottleneck; a faster
engine would allow more replicates per base graph `G0` in the final run. Both
lines require further investigation and will be recorded in `docs/` once
decided.

## Design at a glance

- Two groups `A` and `B`; a node joins `A` with probability `p`.
- Homophily weight `h`, with a degree bag and rejection sampling for attachment.
- Two-phase growth: `N1 = 250` nodes in phase 1 and `N2 = 250` in phase 2, so
  `N = 500`.
- Factor grids `H`, `P`, and `M` crossed, giving 75 baselines `(h1, p1, m)`;
  `Phi` is applied to every network.
- Full intervention grid: 24 interventions plus one control per baseline.
- Pilot replication `R = 50`, that is, 93,750 networks and 187.5 million cascades.

## Structure

```
src/bah_cascade/   package
tests/             test suite
docs/              specification and contracts
notebooks/         demonstration and analysis notebooks
results/           generated datasets (ignored by git)
reports/           derived analyses and figures (ignored by git)
```

## Setup

```powershell
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Python 3.14 is the reference interpreter, pinned in `.python-version` and required
by `pyproject.toml`. Dependencies are managed with `uv` and locked in `uv.lock`.

## Documentation

- `AGENTS.md` — working rules.
- `docs/model.md` — model specification.
- `docs/data-contracts.md` — CSV contracts.
- `docs/roadmap.md` — phase status and exit criteria.
