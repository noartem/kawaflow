# Context7 MCP Integration

## Automatic Documentation Retrieval

Context7 MCP is configured to automatically provide up-to-date library documentation when working with external dependencies. The system will automatically fetch relevant documentation without requiring explicit requests.

## Auto-Trigger Scenarios

Context7 will automatically activate when:

- **Code examples requested** - When users ask for implementation examples or code snippets
- **Setup/configuration steps** - When discussing library installation, configuration, or setup procedures
- **Library/API documentation** - When referencing external libraries, frameworks, or APIs
- **Integration guidance** - When implementing third-party service integrations
- **Best practices** - When discussing recommended patterns for specific libraries

## Supported Libraries for Kawaflow

Context7 can provide documentation for all major dependencies used in this project:

### Python Libraries

- **FastAPI** - Web framework documentation and examples
- **Socket.IO** - WebSocket implementation patterns
- **Docker SDK** - Container management API reference
- **Uvicorn** - ASGI server configuration
- **Pytest** - Testing framework best practices
- **Ruff** - Linting and formatting configuration

### Development Tools

- **UV** - Package management and virtual environment setup
- **Docker** - Containerization best practices and Dockerfile optimization

## Usage Pattern

When discussing any external library or asking for implementation help, Context7 will automatically:

1. Resolve the library to get the most current documentation
2. Fetch relevant sections based on the conversation context
3. Provide accurate, up-to-date examples and configuration guidance
4. Include best practices and common patterns

No explicit "use context7" requests are needed - the system handles this transparently based on conversation context and detected library references.
