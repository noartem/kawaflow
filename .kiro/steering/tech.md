# Technology Stack

## Languages & Frameworks

**Python 3.12+** - Primary language for both services

- FastAPI - Web framework for flow-manager service
- Socket.IO - WebSocket communication
- Docker SDK - Container management
- Uvicorn - ASGI server

**Node.js** - Development tooling and utilities

- Repomix - Code analysis
- Google Gemini CLI - AI assistance

## Build System & Package Management

**UV** - Python package manager and virtual environment tool

- Used for dependency management and project builds
- Lock files (uv.lock) ensure reproducible builds
- Integrated with Docker for containerized development

**Task** - Task runner for build automation

- Defined in Taskfiles (root, flow, and flow-manager directories)
- Handles Docker builds, testing, linting, and development workflows
- **IMPORTANT**: All project commands should be run using Taskfile
- **NOTE**: When using sub-folder taskfiles, do NOT use `cd` commands. Instead, use the namespace prefix format: `task flow:test` or `task flow-manager:test`

## Development Tools

**Ruff** - Python linting and formatting
**Ty** - Type checking (alternative to mypy)
**Pytest** - Testing framework

## Common Commands

### Build & Development

```bash
task init          # Install dependencies
task build         # Build all Docker images
task flow:build    # Build flow service
task flow-manager:build  # Build flow-manager service
```

### Testing & Quality

```bash
task test          # Run all tests
task flow:test     # Run flow service tests
task flow-manager:test  # Run flow-manager service tests
task lint          # Run linting on all services
task lint-fix      # Auto-fix linting issues
```

### Specific Test Execution

The test commands support pytest arguments for running specific tests:

```bash
# Run specific test file
task flow:test -- tests/test_actors.py
task flow-manager:test -- tests/test_api.py

# Run specific test function
task flow:test -- tests/test_actors.py::test_specific_function
task flow-manager:test -- tests/test_api.py::test_websocket_connection

# Run with pytest options
task flow:test -- tests/ -v
task flow:test -- tests/ -k "email"
task flow-manager:test -- tests/ --tb=short
```

### Execute Shell Commands

```bash
task flow:sh-exec -- "echo 'foo'"
task flow-manager:sh-exec -- "echo 'bar'"
```

### Python Dependency Management

**CRITICAL**: All Python dependency management MUST be done using UV CLI inside Docker containers.

```bash
# Add new dependencies
task flow:sh-exec -- "uv add package-name"
task flow-manager:sh-exec -- "uv add package-name"

# Add development dependencies
task flow:sh-exec -- "uv add --dev pytest-package"
task flow-manager:sh-exec -- "uv add --dev pytest-package"

# Remove dependencies
task flow:sh-exec -- "uv remove package-name"
task flow-manager:sh-exec -- "uv remove package-name"

# Update dependencies
task flow:sh-exec -- "uv lock --upgrade"
task flow-manager:sh-exec -- "uv lock --upgrade"

# Install dependencies from lock file
task flow:sh-exec -- "uv sync"
task flow-manager:sh-exec -- "uv sync"
```

**Never install Python packages directly on the host system** - always use UV within the appropriate service container.

## Development Workflow

**IMPORTANT**: All code execution, testing, and development tasks MUST be performed inside Docker containers using the Taskfile commands. Never run Python commands directly on the host system.

### Execution Rules

- Use `task flow:sh-exec` or `task flow-manager:sh-exec` for running commands
- All tests run via `task test`, `task flow:test`, or `task flow-manager:test`
- Linting and formatting via `task lint` and `task lint-fix`
- **IMPORTANT**: Never use `cd flow/ && task test` - always use the namespace prefix format: `task flow:test`
- **Testing & Validation**: When you need to test code, imports, or functionality, create test files or temporary scripts and run them using Docker containers via the appropriate task commands

### Why Docker-Only Development

- Ensures consistent Python 3.12+ environment
- UV package manager properly configured
- All dependencies isolated and reproducible
- Socket communication properly configured
- Prevents host system conflicts

## Architecture Patterns

- **Event-driven architecture** with custom actor system
- **Microservices** - Separate flow and flow-manager services
- **Containerized development** - All services run in Docker
- **Socket-based communication** for real-time updates
