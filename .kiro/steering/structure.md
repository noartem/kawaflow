# Project Structure

## Root Level Organization

```
kawaflow/
├── flow/                    # Flow engine service (actor-based workflow system)
│   ├── Taskfile.yml        # Flow service specific tasks
│   └── ...                 # Flow service files
├── flow-manager/           # Container management service (WebSocket API)
│   ├── Taskfile.yml        # Flow-manager service specific tasks
│   └── ...                 # Flow-manager service files
├── .kiro/                  # Kiro AI assistant configuration
├── .github/                # GitHub workflows and templates
├── node_modules/           # Node.js dependencies for tooling
├── Taskfile.yml           # Root task definitions with includes to service taskfiles
└── package.json           # Node.js tooling dependencies
```

## Flow Service Structure

**Purpose**: Event-driven workflow orchestration using custom Kawa framework

```
flow/
├── kawa/                   # Core Kawa framework (custom actor system)
├── tests/                  # Unit and integration tests
├── main.py                # Main application entry point with actor definitions
├── serve.py               # Service startup and configuration
├── pyproject.toml         # Python project configuration
├── uv.lock               # Locked dependencies
├── Taskfile.yml          # Flow service specific tasks
└── Dockerfile            # Container build configuration
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

The project uses a modular taskfile structure:

- Root Taskfile.yml includes service-specific taskfiles
- Each service has its own Taskfile.yml with service-specific tasks
- All project commands should be run using Taskfile
- **IMPORTANT**: When running tasks for a specific service, use the namespace prefix format (e.g., `task flow:test` or `task flow-manager:build`) rather than changing directories

## Development Conventions

### File Naming

- Python files: snake_case
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE

### Service Communication

- Flow services communicate via Unix sockets (`/var/run/kawaflow.sock`)
- Flow-manager exposes WebSocket API on port 8000
- Container port assignments: 8000-9000 range

### Docker Integration

- Each service has its own Dockerfile
- Development happens inside containers
- Volume mounts for live code reloading
- Shared socket files for inter-service communication

### Testing Structure

- Tests mirror source structure
- Use pytest for all Python testing
- Async tests for WebSocket and container operations
- Mock Docker operations in unit tests
