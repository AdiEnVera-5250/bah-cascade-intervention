# Data Contracts

**Version:** 0.1.0
**Schema version:** 1.0
**Status:** normative
**Last updated:** 2026-11-06

This document is the contract between the experiment runner and the analysis
layer. It defines file names, columns, types, keys, invariants, serialization,
and versioning. It does not describe the model (`docs/model.md`) or the
implementation.

## 1. Scope and status

The contract covers the artifacts written under `results/<run_id>/`:

- `metadata.json`;
- `networks.csv`;
- `cascades/<baseline_id>.csv.gz`.

It does not cover configuration files, figures, or derived analysis tables.
Derived tables are deferred to `docs/analysis-contracts.md`. Cascade trajectories
are out of scope: the study is not extended with a `cascade_trajectory.csv`.

Base graphs `G0` are not persisted. They are reconstructed from the recorded
`base_seed` and the phase-1 parameters `(h1, p1, m)`, as specified in Sections 3.6
and 5.5 of `docs/model.md`.

## 2. Versioning

`schema_version` uses `MAJOR.MINOR`.

- **Major:** renaming, removing, or changing the type or semantics of a column;
  changing a primary key; changing the meaning of an existing value.
- **Minor:** adding a nullable column, a new file, or a new enum value.
- **Patch:** documentation only.

The analysis layer rejects a different major version and tolerates minor additions
when the columns it uses are present. Changing this contract requires explicit
approval, as stated in `AGENTS.md`.

## 3. Conventions

- UTF-8 without BOM; comma delimiter; header row; no index column.
- `LF` line endings on every platform.
- Nulls are empty strings; the token `NaN` is not written.
- Booleans are `0` or `1`.
- Floats use the shortest round-trip representation; values are not rounded for
  display.
- Column names are `snake_case` and in English.
- Column order is fixed and documented; rows are sorted by primary key.
- CSVs contain no timestamps and no absolute paths.
- `run_id` is the run directory name, not a column.
- `schema_version` lives only in `metadata.json`; it is not repeated as a column.
- Node identifiers are integers `0..N-1`. Identifiers `0..N1-1` belong to `G0`
  and are the same across all phase-2 networks derived from that `G0`.
  Identifiers `N1..N-1` are the phase-2 arrivals, ordered by arrival step.
- `network_id` values are integers unique within a run, assigned by the runner in
  ascending order of `(m, h1, p1, replicate, h2, p2)`.
- `baseline_id` is `m{m}_h{h1}_p{p1}`, with each float in its shortest round-trip
  decimal form, for example `m1_h0.2_p0.4`.

## 4. Run layout

```
results/<run_id>/
  metadata.json
  networks.csv
  cascades/
    <baseline_id>.csv.gz
```

`run_id = <config_name>__<8-hex config hash>`.

The partition by `baseline_id` is physical. The logical schema is identical across
partitions, and each partition contains every network derived from that baseline,
including its control.

## 5. `metadata.json`

| Field | Type | Description |
|---|---|---|
| `run_id` | string | Run identifier; equal to the directory name |
| `config_name` | string | Name of the named configuration in `config.py` |
| `config_hash` | string | Hash of the resolved configuration |
| `model_version` | string | Version from `docs/model.md` |
| `schema_version` | string | Version of this contract |
| `created_at` | string | ISO 8601 UTC |
| `git_commit` | string | Commit hash at run time |
| `git_dirty` | boolean | Whether the working tree was modified |
| `master_seed` | integer | Master seed for all streams |
| `status` | string | `running`, `completed`, or `failed` |
| `parameters` | object | Fully resolved design: `H`, `P`, `M`, `Phi`, `N1`, `N2`, `N`, `R`, `design`, `baselines`, `interventions_per_baseline` |
| `environment` | object | Python, numpy, pandas, networkx, and platform versions |
| `files` | array | Per file: `path`, `format`, `compression`, `rows`, `sha256` |
| `counts` | object | `networks_expected`, `networks_written`, `cascades_expected`, `cascades_written` |
| `duration_seconds` | number | Wall-clock time |
| `notes` | string | Free text |

`files[].path` is relative to the run directory and uses forward slashes.
`parameters.design` is `full`, `reduced`, or `custom`. `custom` covers any
intervention set that is not the full grid or the reduced behavioral-plus-size
design, including smoke and test configurations.

## 6. `networks.csv`

One row per final network. Base graphs are not stored.

**Primary key:** `network_id`.
**Unique key:** `(baseline_id, replicate, h2, p2)`.

| Column | Type | Null | Description |
|---|---|---|---|
| `network_id` | integer | no | Unique within the run |
| `baseline_id` | string | no | `m{m}_h{h1}_p{p1}` |
| `replicate` | integer | no | Replicate index `1..R` |
| `intervention_type` | string | no | `none`, `behavioral`, `size`, or `mixed`; `none` is the control |
| `control_network_id` | integer | yes | FK to the control of the same baseline and replicate; null for controls |
| `h1` | float | no | Phase-1 homophily |
| `p1` | float | no | Phase-1 probability of group `A` |
| `h2` | float | no | Phase-2 homophily; equals `h1` for controls |
| `p2` | float | no | Phase-2 probability of `A`; equals `p1` for controls |
| `m` | integer | no | Edges per arriving node |
| `N1` | integer | no | Phase-1 size |
| `N2` | integer | no | Phase-2 size |
| `N` | integer | no | Final size |
| `base_seed` | integer | no | Seed used to generate `G0` |
| `intervention_seed` | integer | no | Seed used for phase 2 |
| `n_A` | integer | no | Final number of nodes in `A` |
| `n_B` | integer | no | Final number of nodes in `B` |
| `n_isolated` | integer | no | Nodes of degree zero; must be `0` |
| `n_edges` | integer | no | Number of edges |
| `edges_cross` | integer | no | Edges between `A` and `B` |
| `edges_within_A` | integer | no | Edges inside `A` |
| `edges_within_B` | integer | no | Edges inside `B` |
| `n_components` | integer | no | Number of connected components |
| `largest_component_size` | integer | no | Size of the largest component |
| `k_min` | integer | no | Minimum degree |
| `k_max` | integer | no | Maximum degree |
| `k_mean` | float | no | Mean degree |
| `k_median` | float | no | Median degree |
| `k_min_A` | integer | no | Minimum degree in `A` |
| `k_max_A` | integer | no | Maximum degree in `A` |
| `k_mean_A` | float | no | Mean degree in `A` |
| `k_median_A` | float | no | Median degree in `A` |
| `k_min_B` | integer | no | Minimum degree in `B` |
| `k_max_B` | integer | no | Maximum degree in `B` |
| `k_mean_B` | float | no | Mean degree in `B` |
| `k_median_B` | float | no | Median degree in `B` |
| `frac_A` | float | no | `n_A / N` |

Medians are taken over node degrees. When the count is even, the median is the
arithmetic mean of the two central order statistics.

`baseline_id`, `replicate`, and `base_seed` identify `G0`. `base_seed` must be
constant across all rows that share `(baseline_id, replicate)`.

## 7. `cascades/<baseline_id>.csv.gz`

One row per `(network, seed, phi)`.

**Primary key:** `(network_id, seed_id, phi)`.

| Column | Type | Null | Description |
|---|---|---|---|
| `network_id` | integer | no | FK to `networks.csv` |
| `seed_id` | integer | no | Seed node identifier |
| `seed_group` | string | no | `A` or `B` |
| `seed_degree` | integer | no | Degree of the seed in this network |
| `seed_stage` | string | no | `base` if `seed_id < N1`, otherwise `phase2` |
| `seed_component_size` | integer | no | Size of the seed's connected component |
| `phi` | float | no | Threshold |
| `S_N` | integer | no | Cascade size, including the seed |
| `S_A` | integer | no | Active nodes in `A` |
| `S_B` | integer | no | Active nodes in `B` |
| `S_N_rel` | float | no | `S_N / N` |
| `t_s` | integer | no | Synchronous steps to steady state |
| `is_global` | integer | no | `1` if `S_N > N/2`, else `0` |

Rows are sorted by `(network_id, seed_id, phi)`.

## 8. Physical format

- `metadata.json` is JSON encoded in UTF-8.
- `networks.csv` is plain CSV.
- `cascades/<baseline_id>.csv.gz` is gzip-compressed CSV with compression level 9.
- gzip headers use `mtime=0` and no embedded file name, so the bytes are
  deterministic.
- Parquet is allowed for `cascades` when the row count makes CSV impractical. It
  requires `pyarrow`, which is a new dependency and needs explicit approval
  (`AGENTS.md`). `metadata.json` records `format` and `compression` per file, so
  the analysis layer can dispatch without guessing.
- Partitioning switches from CSV to Parquet only above 10 million rows per
  `baseline_id` partition. In the main design each partition has 2.5 million rows,
  so gzip CSV is the default. If Parquet is adopted, the file is
  `cascades/<baseline_id>.parquet`.

## 9. Invariants and validation

Referential integrity:

- Every `network_id` in `cascades` exists in `networks.csv`.
- Every non-null `control_network_id` exists and has `intervention_type = none`.
- The control and the intervened network share `baseline_id`, `replicate`,
  `base_seed`, `h1`, `p1`, and `m`.

Keys and counts:

- `network_id` is unique.
- `(baseline_id, replicate, h2, p2)` is unique.
- `parameters.baselines` equals the number of distinct `baseline_id` values.
- `parameters.interventions_per_baseline` equals the number of distinct
  `(h2, p2)` values per `(baseline_id, replicate)`, excluding the control.
- `(network_id, seed_id, phi)` is unique.
- Every `(network_id, seed_id)` has exactly `|Phi|` rows.
- Every network has exactly `N x |Phi|` cascade rows.

Network values:

- `n_A > 0` and `n_B > 0`.
- `n_A + n_B = N`.
- `n_isolated = 0`.
- `n_edges = edges_cross + edges_within_A + edges_within_B`.
- `k_mean = 2 * n_edges / N`.
- `k_mean_A = (2 * edges_within_A + edges_cross) / n_A`.
- `k_mean_B = (2 * edges_within_B + edges_cross) / n_B`.
- `n_components >= 1` and `1 <= largest_component_size <= N`.
- `k_min >= m`.
- `k_min = min(k_min_A, k_min_B)` and `k_max = max(k_max_A, k_max_B)`.
- `k_min_A >= m` and `k_min_B >= m`.
- `k_min <= k_median <= k_max`, and the same per group.
- `frac_A = n_A / N`.
- `0 <= h1, h2 <= 1` and `0 <= p1, p2 <= 1`.
- If `intervention_type = none`, then `h2 = h1` and `p2 = p1`.
- If `intervention_type = behavioral`, then `h2 != h1` and `p2 = p1`.
- If `intervention_type = size`, then `h2 = h1` and `p2 != p1`.
- If `intervention_type = mixed`, then `h2 != h1` and `p2 != p1`.

Cascade values:

- `1 <= S_N <= N`.
- `S_N = S_A + S_B`.
- `S_A >= 1` if `seed_group = A`, and `S_B >= 1` if `seed_group = B`.
- `S_N <= seed_component_size`.
- `S_N_rel = S_N / N`.
- `t_s >= 0`.
- `is_global = 1` if and only if `S_N > N/2`.
- `seed_degree >= m`.
- `seed_stage = base` if and only if `seed_id < N1`.

Floating-point equalities above are checked within `1e-12`, because the stored
values use round-trip representation. The per-node group assignment is not
persisted; `seed_group` is its only record in the artifacts.

Validation is performed on load. Missing required columns, a different major
`schema_version`, broken foreign keys, duplicated keys, or violated invariants are
hard errors in the analysis layer.

## 10. Determinism and serialization

- Same seed, same code, and same dependency versions produce byte-identical files.
- Rows are sorted by primary key before writing.
- Column order is fixed.
- Floats are written in shortest round-trip form.
- gzip uses level 9, `mtime=0`, and no embedded file name.
- CSV uses `LF` and UTF-8 without BOM.
- No timestamps or absolute paths inside CSV files.

The network-level paired differences are not stored. They are derived during
analysis from `networks.csv` and `cascades/`, as described in Section 5.4 of
`docs/model.md`.

## 11. Resume and partial runs

- The runner writes to a temporary directory and renames it atomically when the
  run completes.
- `metadata.json.status` reflects `running`, `completed`, or `failed`.
- A resumed run validates `config_hash` and `schema_version` before writing.
- Each `cascades/<baseline_id>.csv.gz` is written only after all of its networks
  are complete.
- The run manifest lists completed `network_id` values; a resume never duplicates
  or overwrites a completed network.

## 12. Row counts

Let `B` be the number of baselines `(h1, p1, m)`, `K` the number of interventions
per baseline, and `R` the number of replicates. With `H`, `P`, and `M` as defined
in `docs/model.md`:

```
B        = |H| x |P| x |M| = 5 x 5 x 3 = 75
networks = B x (K + 1) x R
cascades = networks x N x |Phi|
```

| Design | `B` | `K` | `R` | Networks | Cascades |
|---|---:|---:|---:|---:|---:|
| Full grid (main) | 75 | 24 | 50 | 93,750 | 187,500,000 |
| Reduced | 75 | 8 | 50 | 33,750 | 67,500,000 |
| Behavioral only | 75 | 4 | 50 | 18,750 | 37,500,000 |
| Size only | 75 | 4 | 50 | 18,750 | 37,500,000 |

The main design is the full grid: the 4 behavioral, 4 size, and 16 mixed
interventions per baseline. The reduced design keeps only the 4 behavioral and 4
size interventions. Behavioral-only and size-only runs are recorded as
`design = custom` with `interventions_per_baseline = 4`. Smoke and test
configurations also use `design = custom` and record their own `K`.

For the full grid, each `baseline_id` partition holds

```
25 x 50 networks x 500 seeds x 4 thresholds = 2,500,000 cascade rows.
```

## 13. Examples

`metadata.json` (the `files` array is truncated to two entries for readability):

```json
{
  "run_id": "PILOT__1a2b3c4d",
  "config_name": "PILOT",
  "config_hash": "1a2b3c4d",
  "model_version": "0.2.0",
  "schema_version": "1.0",
  "created_at": "2026-11-06T12:00:00Z",
  "git_commit": "0000000",
  "git_dirty": false,
  "master_seed": 20261106,
  "status": "completed",
  "parameters": {
    "H": [0.0, 0.2, 0.5, 0.8, 1.0],
    "P": [0.2, 0.4, 0.5, 0.6, 0.8],
    "M": [1, 2, 4],
    "Phi": [0.1, 0.15, 0.2, 0.25],
    "N1": 250,
    "N2": 250,
    "N": 500,
    "R": 50,
    "design": "full",
    "baselines": 75,
    "interventions_per_baseline": 24
  },
  "environment": {
    "python": "3.14.0",
    "numpy": "2.3.0",
    "pandas": "2.3.0",
    "networkx": "3.5",
    "platform": "Windows"
  },
  "files": [
    {
      "path": "networks.csv",
      "format": "csv",
      "compression": "none",
      "rows": 93750,
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
    },
    {
      "path": "cascades/m1_h0.2_p0.4.csv.gz",
      "format": "csv",
      "compression": "gzip",
      "rows": 2500000,
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
    }
  ],
  "counts": {
    "networks_expected": 93750,
    "networks_written": 93750,
    "cascades_expected": 187500000,
    "cascades_written": 187500000
  },
  "duration_seconds": 0,
  "notes": ""
}
```

`networks.csv`:

```csv
network_id,baseline_id,replicate,intervention_type,control_network_id,h1,p1,h2,p2,m,N1,N2,N,base_seed,intervention_seed,n_A,n_B,n_isolated,n_edges,edges_cross,edges_within_A,edges_within_B,n_components,largest_component_size,k_min,k_max,k_mean,k_median,k_min_A,k_max_A,k_mean_A,k_median_A,k_min_B,k_max_B,k_mean_B,k_median_B,frac_A
1,m1_h0.2_p0.4,1,none,,0.2,0.4,0.2,0.4,1,250,250,500,101,201,200,300,0,502,210,67,225,1,500,1,35,2.008,1.0,1,12,1.72,1.0,1,35,2.2,1.0,0.4
2,m1_h0.2_p0.4,1,behavioral,1,0.2,0.4,0.8,0.4,1,250,250,500,101,202,200,300,0,502,80,120,302,1,500,1,35,2.008,1.0,1,12,1.6,1.0,1,35,2.28,1.0,0.4
```

`cascades/m1_h0.2_p0.4.csv.gz`, decompressed:

```csv
network_id,seed_id,seed_group,seed_degree,seed_stage,seed_component_size,phi,S_N,S_A,S_B,S_N_rel,t_s,is_global
1,0,A,3,base,500,0.1,3,2,1,0.006,2,0
1,0,A,3,base,500,0.15,2,1,1,0.004,1,0
```

## 14. Open decisions

1. **Parquet adoption.** Requires `pyarrow`, which needs explicit approval. Until
   then, `cascades` uses gzip CSV.
2. **Final `R`.** The pilot value is `R = 50`; the final value comes from the power
   analysis at the level of `G0` (`docs/model.md`, Section 5.3).
