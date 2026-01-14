# AGENTS

This repo is a multi-service stack (Docker + Task) with Python (kawa, flow, flow-manager), Laravel/Vue UI, docs, and a Docker-driven E2E suite.

If you’re an agent, **prefer Task targets over `cd` + raw commands** to keep environment, mounts, and Python tooling consistent.

## Quick Map

- `flow/`: actor-based workflow engine (built as Docker image).
- `kawa/`: shared Python package (Ruff + ty + pytest).
- `flow-manager/`: FastAPI control plane (Ruff + ty + pytest).
- `ui/`: Laravel 12 + Vue + Vite (php artisan + npm).
- `docs/`: MkDocs site.
- `e2e/`: Docker Compose + pytest E2E tests and HTML reports.

## Tooling Rules

- **Do not run Python tooling directly on the host.** Use `task ...:sh-exec` targets (Docker + UV).
- Prefer `task compose:*` wrappers instead of raw `docker compose ...`.
- Keep generated artifacts inside service directories (avoid root pollution).
- Never commit secrets: `.env`, credentials, tokens, generated reports.

## Build / Run (common)

- Initialize helper tooling: `task init`
- Build stack images: `task build`
- Bring up dev stack: `task compose:up`
- Tear down stack: `task compose:down`
- Rebuild from scratch: `task compose:rebuild`
- Tail logs: `task compose:logs -- <service>`

Local dev endpoints (via Traefik):

- UI: `http://kawaflow.localhost` (Vite HMR uses `:5173`)
- Flow Manager: `http://flow-manager.kawaflow.localhost`
- RabbitMQ UI: `http://rabbitmq.kawaflow.localhost`
- Traefik dashboard: `http://traefik.kawaflow.localhost`

Repo helper tasks:

- `task repomix` (codebase snapshot/analysis)
- `task gemini` (Gemini CLI)
- `task act` (run GitHub Actions locally)

### Service images

- `task flow:build`
- `task kawa:build`
- `task flow-manager:build`
- `task docs:build`
- `task e2e:build`

## Lint / Format

### Python (kawa, flow-manager)

- Lint (Ruff): `task kawa:ruff` / `task flow-manager:ruff`
- Type check (ty): `task kawa:ty` / `task flow-manager:ty`
- Fix formatting + autofixes: `task kawa:lint-fix` / `task flow-manager:lint-fix`

Repo-level aggregations:

- `task lint` currently runs `kawa:lint` (flow-manager lint is commented out).
- `task lint-fix` currently runs `kawa:lint-fix`.

### UI (Laravel/Vue)

UI lint/format tools exist, but are typically run inside the compose container:

- Frontend formatting: `task ui:sh-execute -- "npm run format"`
- Frontend lint fix: `task ui:sh-execute -- "npm run lint"`
- Check formatting only: `task ui:sh-execute -- "npm run format:check"`
- PHP formatter (Pint): `task ui:sh-execute -- "./vendor/bin/pint"`

## Tests

### Run all tests

- `task test`
  - Runs: `flow:test`, `kawa:test`, `ui:test`.
  - Note: `flow:test` is a quick smoke-check command, not a pytest suite.
  - `flow-manager:test` is currently commented out in the root Taskfile.

### Python unit/integration tests

- `task kawa:test`
- `task flow-manager:test`

**Run a single pytest file** (pass-through args after `--`):

- `task kawa:test -- tests/test_registry.py`
- `task flow-manager:test -- tests/test_event_handler.py`

**Run a single test function (node id):**

- `task kawa:test -- tests/test_registry.py::test_dump_is_stable -vv`
- `task flow-manager:test -- tests/test_event_handler.py::test_dispatch_unknown_action -vv`

**Run by keyword:**

- `task flow-manager:test -- -k websocket -vv`

Notes:

- `kawa`/`flow-manager` tests run in Docker with `PYTHONPATH=/app`.
- Prefer explicit node ids for reliability when iterating.

### UI tests (Laravel)

- `task ui:test`

**Run a single test class or method:**

- `task ui:test -- --filter SomeTest`
- `task ui:test -- --filter SomeTest::test_it_does_the_thing`

**Run a single file:**

- `task ui:test -- tests/Feature/Auth/LoginTest.php`

### E2E tests

The E2E suite runs a dedicated compose stack (`e2e/compose.yml`) and executes pytest in the `e2e` service.

- Full E2E run (build → up → migrate → test → down): `task e2e:default`
- Run just E2E tests (also generates HTML report): `task e2e:test`

**Run a single E2E test (bypassing the report wrapper):**

- `task e2e:pytest -- -k "graph" -vv`
- `task e2e:pytest:node -- tests/test_flow_lifecycle.py::test_flow_start_stop`

Artifacts:

- HTML reports are written under `e2e/reports/`.

## Code Style Guidelines

### Python (kawa, flow-manager, e2e)

- Target Python: **3.12+**.
- Formatting: `ruff format`, line length **88**.
- Linting: `ruff check .` (use `task ...:lint-fix` to format + apply autofixes).
- Types: `ty check` is the preferred type checker.
- Prefer modern typing: `dict[str, Any]`, `list[str]`, `str | None`.
- Avoid `Any` unless unavoidable; constrain with Protocols/TypedDict/Pydantic models.

Imports and modules:

- `flow-manager/` is a flat module layout; imports are typically `from models import ...` (not package-prefixed).
- `kawa/` is a proper package (`kawa/kawa/*`); use package-relative imports (`from .utils import ...`) consistent with existing code.

Error handling & logging:

- In FastAPI routes, translate operational errors into `HTTPException` with appropriate status codes.
- In message/worker flows (`EventHandler`), publish standardized error payloads (see `flow-manager/models.py` `ErrorResponse`) and log with context.
- Prefer logging exceptions with structured context dicts (see `SystemLogger.error(exc, {...})`) over `print()`.
- Don’t swallow exceptions unless you have a clear fallback; if you catch broad exceptions, either re-raise or emit a well-typed error response.

Async:

- Use `async`/`await` consistently; avoid blocking calls in async loops.
- If you must poll or sleep, ensure cancellation is handled (`asyncio.CancelledError`).

### PHP (ui)

- Follow Laravel conventions (controllers, requests, jobs, etc.).
- Use `php artisan ...` through Task/compose to match container PHP extensions.
- Formatting: use Laravel Pint (`./vendor/bin/pint`) when touching PHP.
- Tests: prefer `php artisan test` (Pest is present via composer).

### TypeScript/Vue (ui)

- Formatting: Prettier (`npm run format`) and check (`npm run format:check`).
- Lint: ESLint (`npm run lint`).
- Prefer explicit types for public APIs and component props; avoid implicit `any`.

## Repo-Specific Testing Expectations

- `flow` constructs an internal actor graph at runtime (actors as nodes, events as edges).
- E2E coverage should validate the **runtime** graph (via flow-manager/containers) matches the code-derived structure, not only UI graph JSON.

## Editor/Assistant Rules

- Cursor rules: none found in `.cursor/rules/` or `.cursorrules`.
- Copilot rules: none found at `.github/copilot-instructions.md`.
