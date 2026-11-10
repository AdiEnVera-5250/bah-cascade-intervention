# AGENTS.md

## Scope

Research project on network growth with homophily, phased group interventions, and
threshold cascades. The scientific specification lives in `docs/model.md`. This
file governs only how work is done in this repository.

## Language

All repository content is in English: code, identifiers, docstrings, comments,
documentation, commit messages, error messages, log messages, test names, and
filenames. No other language is permitted.

## Source of truth

1. `AGENTS.md` — working rules.
2. `docs/model.md` — model, assumptions, and parameters.
3. `docs/data-contracts.md` — CSV columns and `schema_version`.
4. `docs/roadmap.md` — phase status.

If two documents conflict, the lower number prevails. If that rule does not
resolve the conflict, stop and ask.

## Branch

- `main` is the only working branch. All work is committed there.
- Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`), one topic
  per commit.
- Never rewrite history or force-push.
- No opportunistic refactors or reformatting. Do not touch files unrelated to the
  task.

## Ambiguity and contradictions

- If a request is ambiguous, contradictory, or underspecified, do not guess. Stop
  before changing files and return a short numbered list of concrete questions
  (at most five), each stating the decision required and the available options.
- If the request conflicts with this file or with `docs/`, state the conflict
  explicitly and ask before proceeding.
- Read `docs/model.md` first. Ask only about what is genuinely unspecified there.
- Never resolve ambiguity by choosing a default silently.

## Requires explicit approval

- Adding or updating dependencies.
- Changing public interfaces or data contracts.
- Modifying `docs/model.md`, `docs/data-contracts.md`, or the RNG module.
- Changing architecture, directory structure, or module names.
- Altering scientific assumptions or default model parameters.
- Writing outside the paths named in the task.
- Adding a top-level directory.

## Implementation

- Python with `src/` layout.
- `snake_case` for modules, functions, and variables; `PascalCase` only for
  classes; `UPPER_SNAKE_CASE` for constants.
- Type hints on every public function and on non-trivial internal functions.
- No magic numbers: parameters arrive through configuration.
- Comments only for non-obvious decisions (mathematics, reproducibility,
  algorithms). Never restate the code.
- Small functions; keep generation, simulation, metric computation, and
  persistence separate.
- `logging`, never `print`, except in user-facing scripts.
- Run artifacts are written only by the experiment runner. Analysis reads
  `results/` and writes only to `reports/`.
- Documentation lives in `docs/`. Do not create per-directory README files; if a
  directory needs explanation, add it to `docs/`.

## Reproducibility

- Every stochastic process receives an explicit `numpy.random.Generator`.
- Never use the global state of `numpy.random` or `random`.
- Sequences derive from a master seed through `SeedSequence`.
- Seed and resolved parameters are recorded in run metadata.

## Tests

- A test exists to detect the breakage of an invariant, a rule, or a contract. If
  it cannot fail, it is not written.
- Prohibited: tautologies, comparing a function with its own formula, trivial
  snapshots, tests that only assert that no exception is raised (unless "no
  exception" is the contract), and tests of the standard library or third-party
  libraries.
- Expected values are computed by hand on small cases; never copied from the
  implementation.
- Every fixed bug leaves a regression test.
- Never weaken an assertion to make a test pass. If test and code disagree,
  decide which is correct from `docs/model.md`; if it is not evident, ask.
- One behavior per test. Name: `test_<subject>_<expected>_when_<condition>`.
- Unit tests touch neither the network nor the filesystem. Integration tests use
  `tmp_path` and small graphs.
- Stochastic cases use a fixed seed and an exact assertion, or a justified wide
  tolerance. No tight statistical assertions.

## Verification

Before declaring a task done, run:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

If any of them fails, the task is not done.

## Hygiene

- Do not commit datasets, figures, logs, or artifacts.
- Keep the root minimal: project metadata, package source, tests, docs, notebooks,
  and configuration modules only.
- One dependency manager only: `uv`, with `uv.lock` committed.
- One Python version, pinned in `.python-version`.

## Current phase

Do not start a phase without explicit authorization. Phase status lives in
`docs/roadmap.md`. Model implementation does not start until `docs/model.md`
exists.

## Definition of done

- The change addresses exactly the requested task.
- New or updated tests cover the invariant that was touched.
- `docs/` is updated only if a contract, assumption, or decision changed.
- `ruff` and `pytest` pass.
- No generated artifacts in the diff.
