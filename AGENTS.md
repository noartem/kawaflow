# Repository Guidelines

## Project Structure & Module Organization
- Services: `flow/` (actor-based workflow engine on Kawa), `flow-manager/` (FastAPI + Socket.IO container control plane), `kawa/` (shared Python package), and `docs/` (MkDocs site). `.kiro/steering` holds product/tech guidance; keep it in sync.
- Root `Taskfile.yml` includes service taskfiles; always invoke tasks with prefixes (`task flow:test`, `task flow-manager:build`) instead of `cd`.
- Tests live in `flow-manager/tests` and `kawa/tests`; Dockerfiles per service; root `.env` for local secrets (never commit).

## Build, Test, and Development Commands
- Install tooling: `task init` (npm-based helpers). All Python work happens via Task inside Docker with UV; target Python 3.12+.
- Build: `task build` for all images; or `task flow:build`, `task flow-manager:build`, `task kawa:build`, `task docs:build` individually.
- Quality: `task lint` (ruff + type checking); `task lint-fix` to autoformat/fix. Dependency changes must use UV inside containers (`task flow:sh-exec -- "uv add pkg"`).
- Tests: `task test` runs all; filter with pytest args (`task flow-manager:test -- tests/test_api.py -k websocket`). Docs preview: `task docs:serve` (localhost:8000).

## Coding Style & Naming Conventions
- Python style via Ruff (88 cols) and `ty` type checker; keep explicit type hints. Naming: snake_case for files/functions/vars, PascalCase for classes, UPPER_SNAKE_CASE for constants.
- Prefer small, focused modules per service; keep imports sorted, remove dead code, and run `task lint-fix` before commits.

## Testing Guidelines
- Framework: pytest; test files `test_*.py` mirroring source (e.g., `kawa/tests/test_registry.py` for `kawa/registry.py`). Include unit, integration, and async WebSocket tests for flow-manager; mock Docker SDK where practical.
- Add tests for every feature/bugfix; keep them independent and cover success + error paths. Use standard pytest options through Task (`-k`, `-v`, specific node ids).

## Commit & Pull Request Guidelines
- Commit style matches history: Conventional Commit verbs with scopes when relevant (`feat:`, `refactor(kawa):`, `feat(dev):`). Reference services in scopes (`flow-manager`, `kawa`, `docs`).
- PRs: clear description, linked issues, impacted services, and required proofs (lint/test outputs: `task lint`, `task test`). Attach screenshots for docs/UI changes when relevant; avoid bundling unrelated changes.

## Security & Operations
- Never run Python tooling directly on host; use Task + Docker to ensure UV-managed, reproducible environments. Keep secrets in `.env` and inject via tasks/containers; avoid shelling out with unsanitized inputs in FastAPI handlers.
- Containers expose WebSocket API on :8000 and Unix socket communication for flow; keep generated artifacts within service directories to prevent root pollution.
