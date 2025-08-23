# Project Structure

## Root Level Organization

```
kawaflow/
├── flow/                    # Flow examples and test scripts
│   ├── examples/           # Example flow implementations
│   ├── Taskfile.yml        # Flow service specific tasks
│   ├── test.py            # Test script for Kawa framework
│   └── Dockerfile         # Container build configuration
├── flow-manager/           # Container management service (WebSocket API)
│   ├── main.py            # FastAPI application with Socket.IO
│   ├── pyproject.toml     # Python project configuration
│   ├── uv.lock           # Locked dependencies
│   ├── Taskfile.yml      # Flow-manager service specific tasks
│   └── Dockerfile        # Container build configuration
├── kawa/                   # Core Kawa framework package (custom actor system)
│   ├── kawa/              # Main package source code
│   ├── tests/             # Unit and integration tests
│   ├── pyproject.toml     # Python project configuration
│   ├── uv.lock           # Locked dependencies
│   ├── Taskfile.yml      # Kawa package specific tasks
│   └── Dockerfile        # Container build configuration
├── docs/                   # Documentation site (MkDocs)
├── .kiro/                  # Kiro AI assistant configuration
├── .github/                # GitHub workflows and templates
├── node_modules/           # Node.js dependencies for tooling
├── Taskfile.yml           # Root task definitions with includes to service taskfiles
└── package.json           # Node.js tooling dependencies
```

## Kawa Framework Structure

**Purpose**: Custom actor-based event processing framework

```
kawa/
├── kawa/                   # Main package source
│   ├── __init__.py        # Package initialization and exports
│   ├── core.py           # Core actor system implementation
│   ├── cron.py           # Cron event handling
│   ├── email.py          # Email event handling
│   ├── main.py           # Main framework entry point
│   ├── registry.py       # Actor and event registry
│   ├── serve.py          # Service startup and configuration
│   └── utils.py          # Utility functions
├── tests/                 # Unit and integration tests
├── pyproject.toml        # Python project configuration (setuptools)
├── uv.lock              # Locked dependencies
├── Taskfile.yml         # Kawa package specific tasks
└── Dockerfile           # Container build configuration
```

## Flow Examples Structure

**Purpose**: Example implementations and test scripts using Kawa framework

```
flow/
├── examples/              # Example flow implementations
│   └── daily-weather.py  # Weather data flow example
├── test.py               # Test script for Kawa framework functionality
├── Taskfile.yml         # Flow service specific tasks
└── Dockerfile           # Container build configuration
```

## Flow-Manager Service Structure

**Purpose**: Docker container lifecycle management via WebSocket API

```
flow-manager/
├── main.py                # FastAPI application with Socket.IO
├── pyproject.toml         # Python project configuration
├── uv.lock               # Locked dependencies
├── Taskfile.yml          # Flow-manager service specific tasks
└── Dockerfile            # Container build configuration
```

## Task Management

The project uses a modular taskfile structure with namespace includes:

- Root Taskfile.yml includes service-specific taskfiles with namespaces:
  - `npm:` - Node.js tooling tasks
  - `docs:` - Documentation build tasks
  - `flow:` - Flow examples and testing tasks
  - `flow-manager:` - Container management service tasks
  - `kawa:` - Kawa framework package tasks
- Each service has its own Taskfile.yml with service-specific tasks
- All project commands should be run using Taskfile
- **IMPORTANT**: When running tasks for a specific service, use the namespace prefix format (e.g., `task flow:test`, `task flow-manager:build`, `task kawa:lint`) rather than changing directories

## Development Conventions

### File Naming

- Python files: snake_case
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE

### Architecture Components

- **Kawa Framework**: Standalone Python package providing actor-based event processing
- **Flow Examples**: Test scripts and example implementations using Kawa
- **Flow-Manager**: WebSocket API service for Docker container lifecycle management
- **Documentation**: MkDocs-based documentation site

### Service Communication

- Flow-manager exposes WebSocket API on port 8000
- Container port assignments: 8000-9000 range
- Kawa framework is used as a dependency in flow implementations

### Docker Integration

- Each component has its own Dockerfile for containerized development
- Development happens inside containers using task commands
- Volume mounts for live code reloading
- UV package manager used for Python dependency management

### Testing Structure

- Tests located in respective `tests/` directories
- Use pytest for all Python testing
- Kawa framework has comprehensive test suite
- Flow examples use test.py for validation
- Async tests for WebSocket and container operations in flow-manager
