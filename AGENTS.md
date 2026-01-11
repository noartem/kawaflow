# Repository Guidelines

## Project Structure & Module Organization
- Services: `flow/` (actor-based workflow engine on Kawa), `flow-manager/` (FastAPI + Socket.IO control plane), `kawa/` (shared Python package), `ui/` (Laravel frontend), and `docs/` (MkDocs site).
- Root `Taskfile.yml` includes service taskfiles; always invoke tasks with prefixes (`task flow:test`, `task flow-manager:build`, `task ui:test`) instead of `cd`.
- Root `compose.yml` defines the local stack (Traefik, Postgres, Redis, RabbitMQ, flow-manager, ui); use the Task wrappers for lifecycle.
- Tests live in `flow-manager/tests`, `kawa/tests`, and `ui/tests`; Dockerfiles per service; root `.env` for local secrets (never commit).

## Build, Test, and Development Commands
- Install tooling: `task init` (npm-based helpers). All Python work happens via Task inside Docker with UV; target Python 3.12+. UI commands run via the compose-backed Task targets (not directly on host).
- Build: `task build` builds kawa/flow/flow-manager dev images; service builds via `task flow:build`, `task flow-manager:build`, `task kawa:build`, `task docs:build`. Bring up the stack with `task compose:up` (Traefik at `traefik.kawaflow.localhost`, UI at `kawaflow.localhost`).
- Quality: `task lint` (ruff + type checking); `task lint-fix` to autoformat/fix. Dependency changes must use UV inside containers (`task flow:sh-exec -- "uv add pkg"`).
- Tests: `task test` runs Python suites; filter with pytest args (`task flow-manager:test -- tests/test_api.py -k websocket`). UI tests via `task ui:test -- --filter MyTest` (phpunit). Docs preview: `task docs:serve` (localhost:8000).
- Compose helpers: `task compose:up|down|restart|rebuild` wrap `docker compose -f compose.yml ...`; prefer these over raw docker commands to keep env consistent.

## Coding Style & Naming Conventions
- Python style via Ruff (88 cols) and `ty` type checker; keep explicit type hints. Naming: snake_case for files/functions/vars, PascalCase for classes, UPPER_SNAKE_CASE for constants.
- Prefer small, focused modules per service; keep imports sorted, remove dead code, and run `task lint-fix` before commits.

## Testing Guidelines
- Framework: pytest; test files `test_*.py` mirroring source (e.g., `kawa/tests/test_registry.py` for `kawa/registry.py`). Include unit, integration, and async WebSocket tests for flow-manager; mock Docker SDK where practical.
- UI uses phpunit in `ui/tests`; run via `task ui:test` and filter with `--filter` when needed.
- Add tests for every feature/bugfix; keep them independent and cover success + error paths. Use standard pytest options through Task (`-k`, `-v`, specific node ids).
- Flows generate an internal actor graph at runtime (actors as nodes, events as edges) from Python code; e2e tests must validate the runtime actor graph matches the code-derived structure, not just the UI graph JSON.

## Security & Operations
- Never run Python tooling directly on host; use Task + Docker to ensure UV-managed, reproducible environments. Run UI tooling through the compose-based tasks (artisan/composer via `task ui:*`) instead of host binaries. Keep secrets in `.env` and inject via tasks/containers; avoid shelling out with unsanitized inputs in FastAPI handlers.
- Containers expose WebSocket API on :8000 and Unix socket communication for flow; keep generated artifacts within service directories to prevent root pollution.
