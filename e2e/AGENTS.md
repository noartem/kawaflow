# e2e/AGENTS

This directory contains docker-compose-driven end-to-end tests and an HTML report generator.

## How E2E Runs

- Compose file: `e2e/compose.yml`
- Python project: `e2e/pyproject.toml` (pytest config points at `e2e/tests`)
- Runner script (creates report): `e2e/scripts/run_e2e_with_report.py`
- Reports output: `e2e/reports/`

## Commands

Preferred entrypoints are Task targets from repo root.

### Full E2E workflow

- `task e2e:default`
  - Builds E2E images, starts stack, runs migrations, runs tests, tears down.

### Build/Up/Down

- Build images: `task e2e:build`
- Start stack: `task e2e:up`
- Stop stack: `task e2e:down`
- Run DB migrations in the UI container: `task e2e:migrate`

### Run tests (with report)

- `task e2e:test`
  - Runs `uv run python /app/scripts/run_e2e_with_report.py` inside the `e2e` service.
  - Writes an HTML report to `e2e/reports/`.

### Run a single test / faster iteration

Use the dedicated pytest tasks (they skip the HTML report):

- Keyword selection:
  - `task e2e:pytest -- -k "lifecycle" -vv`
  - `task e2e:pytest:k -- "lifecycle"`

- Node id / single test:
  - `task e2e:pytest:node -- tests/test_flow_lifecycle.py::test_flow_start_stop`

- Single file:
  - `task e2e:pytest:node -- tests/test_scenarios.py`

- Re-run failures:
  - `task e2e:pytest:lf`

Tip: the `e2e` service is run ephemerally (via `docker compose run`), so for manual inspection bring the stack up with `task e2e:up`, then use `task e2e:compose -- exec -T <service> <cmd>`.


## Code Style

- Python 3.12+.
- Keep tests deterministic: avoid hard sleeps; prefer polling with timeouts.
- Use `httpx` clients and explicit timeouts for UI/flow-manager calls.
- Use `tenacity` (already in deps) for retryable operations (service warmup, eventual consistency).
- Validate actor graph structure (see `e2e/tests/helpers/graph_validation.py`) and compare hashes when appropriate.

## Cleanup / Safety

- E2E runner cleans up flow containers labeled with `kawaflow.test_run_id=$E2E_TEST_RUN_ID`.
- Don’t commit `e2e/reports/*` or `.pytest_cache/*` artifacts.
- Treat Docker as shared state: label containers and clean them on failures.
