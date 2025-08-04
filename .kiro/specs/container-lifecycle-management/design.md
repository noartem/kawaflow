# Design Document

## Overview

The container lifecycle management system provides comprehensive Docker container management capabilities through a Socket.IO-based API. The system consists of a flow-manager service that handles container operations and communication via Unix sockets, with real-time updates delivered through WebSocket connections.

The architecture follows a simple, event-driven pattern where Socket.IO events trigger container operations, and responses are emitted back to connected clients. Each flow container communicates with flow-manager through dedicated Unix socket files named by container ID.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    Socket.IO     ┌─────────────────┐
│   Client Apps   │ ◄──────────────► │  Flow-Manager   │
└─────────────────┘                  └─────────────────┘
                                              │
                                              │ Docker API
                                              ▼
                                     ┌─────────────────┐
                                     │  Docker Engine  │
                                     └─────────────────┘
                                              │
                                              │ Unix Sockets
                                              ▼
                                     ┌─────────────────┐
                                     │ Flow Containers │
                                     │  {id}.sock      │
                                     └─────────────────┘
```

### Component Interaction Flow

1. **Client Request**: Client sends Socket.IO event to flow-manager
2. **Container Operation**: Flow-manager performs Docker operation via Docker SDK
3. **Socket Communication**: Flow-manager communicates with containers via Unix sockets
4. **Response**: Flow-manager emits Socket.IO response to client
5. **Logging**: All operations are logged with appropriate detail levels

## Components and Interfaces

### Container Manager

**Purpose**: Core container lifecycle management

**Responsibilities**:

- Create, start, stop, restart, update, and delete containers
- Manage Unix socket files for container communication
- Handle container state tracking
- Coordinate with Docker SDK

**Interface**:

```python
class ContainerManager:
    async def create_container(self, config: ContainerConfig) -> ContainerInfo
    async def start_container(self, container_id: str) -> None
    async def stop_container(self, container_id: str) -> None
    async def restart_container(self, container_id: str) -> None
    async def update_container(self, container_id: str, code_path: str) -> None
    async def delete_container(self, container_id: str) -> None
    async def get_container_status(self, container_id: str) -> ContainerStatus
    async def list_containers(self) -> List[ContainerInfo]
```

### Socket Communication Handler

**Purpose**: Manage Unix socket communication with flow containers

**Responsibilities**:

- Establish and maintain Unix socket connections
- Send messages to containers
- Receive messages from containers
- Handle connection errors and timeouts

**Interface**:

```python
class SocketCommunicationHandler:
    async def send_message(self, container_id: str, message: dict) -> None
    async def receive_message(self, container_id: str, timeout: int = 30) -> dict
    async def setup_socket(self, container_id: str) -> None
    async def cleanup_socket(self, container_id: str) -> None
    def is_socket_connected(self, container_id: str) -> bool
```

### Socket.IO Event Handler

**Purpose**: Handle Socket.IO events and coordinate responses

**Responsibilities**:

- Process incoming Socket.IO events
- Validate event data
- Coordinate with ContainerManager
- Emit responses and status updates
- Handle error conditions

**Interface**:

```python
class SocketIOEventHandler:
    async def handle_create_container(self, sid: str, data: dict) -> None
    async def handle_start_container(self, sid: str, data: dict) -> None
    async def handle_stop_container(self, sid: str, data: dict) -> None
    async def handle_restart_container(self, sid: str, data: dict) -> None
    async def handle_update_container(self, sid: str, data: dict) -> None
    async def handle_delete_container(self, sid: str, data: dict) -> None
    async def handle_send_message(self, sid: str, data: dict) -> None
    async def handle_get_status(self, sid: str, data: dict) -> None
    async def handle_list_containers(self, sid: str, data: dict) -> None
```

### System Logger

**Purpose**: Comprehensive system logging for debugging and monitoring

**Responsibilities**:

- Log container operations with detailed technical information
- Log Socket.IO events and responses with full context
- Log Unix socket communication for debugging
- Log errors with full stack traces and context
- Provide structured logging for system debugging

**Interface**:

```python
class SystemLogger:
    def log_container_operation(self, operation: str, container_id: str, details: dict) -> None
    def log_socket_event(self, event: str, sid: str, data: dict) -> None
    def log_communication(self, container_id: str, direction: str, message: dict) -> None
    def log_error(self, error: Exception, context: dict) -> None
    def log_state_change(self, container_id: str, old_state: str, new_state: str) -> None
    def log_debug(self, message: str, context: dict) -> None
```

### User Activity Logger

**Purpose**: User-friendly activity logging sent via Socket.IO

**Responsibilities**:

- Log user-visible container events (created, started, stopped, etc.)
- Log container messages and actor events
- Send activity logs to clients via Socket.IO
- Format logs for user consumption
- Filter sensitive information from user logs

**Interface**:

```python
class UserActivityLogger:
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio

    async def log_container_created(self, container_id: str, name: str) -> None
    async def log_container_started(self, container_id: str, name: str) -> None
    async def log_container_stopped(self, container_id: str, name: str) -> None
    async def log_container_message(self, container_id: str, message: dict) -> None
    async def log_actor_event(self, container_id: str, actor: str, event: str) -> None
    async def log_user_activity(self, activity_type: str, container_id: str, message: str, details: dict = None) -> None
```

## Data Models

### Container Configuration

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class ContainerConfig(BaseModel):
    image: str = Field(..., description="Docker image name")
    name: Optional[str] = Field(None, description="Container name")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    volumes: Dict[str, str] = Field(default_factory=dict, description="Volume mounts")
    ports: Dict[str, int] = Field(default_factory=dict, description="Port mappings")
    command: Optional[List[str]] = Field(None, description="Command to run")
    working_dir: Optional[str] = Field(None, description="Working directory")
```

### Container Information

```python
class ContainerInfo(BaseModel):
    id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    status: str = Field(..., description="Container status")
    image: str = Field(..., description="Docker image")
    created: datetime = Field(..., description="Creation timestamp")
    socket_path: str = Field(..., description="Unix socket path")
    ports: Dict[str, int] = Field(default_factory=dict, description="Port mappings")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
```

### Container Status

```python
from enum import Enum

class ContainerState(Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"

class ContainerHealth(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    NONE = "none"

class ContainerStatus(BaseModel):
    id: str = Field(..., description="Container ID")
    state: ContainerState = Field(..., description="Container state")
    health: ContainerHealth = Field(..., description="Container health")
    uptime: Optional[timedelta] = Field(None, description="Container uptime")
    socket_connected: bool = Field(..., description="Socket connection status")
    last_communication: Optional[datetime] = Field(None, description="Last communication timestamp")
    resource_usage: Dict[str, Any] = Field(default_factory=dict, description="Resource usage metrics")
```

### Socket.IO Event Data Models

```python
# Create Container Event
{
    "image": "flow:latest",
    "name": "optional-name",
    "environment": {"KEY": "value"},
    "volumes": {"/host/path": "/container/path"},
    "ports": {"8080": 8080}
}

# Container Operation Events
{
    "container_id": "container_id_here"
}

# Update Container Event
{
    "container_id": "container_id_here",
    "code_path": "/path/to/new/code"
}

# Send Message Event
{
    "container_id": "container_id_here",
    "message": {"command": "dump", "data": {}}
}
```

## Error Handling

### Error Categories

1. **Docker API Errors**: Container not found, image not available, resource constraints
2. **Socket Communication Errors**: Connection timeout, socket file missing, permission issues
3. **Validation Errors**: Invalid event data, missing required fields
4. **System Errors**: Disk space, memory constraints, network issues

### Error Response Format

```python
{
    "error": True,
    "error_type": "docker_api_error",
    "message": "Container not found",
    "details": {
        "container_id": "abc123",
        "operation": "start_container"
    },
    "timestamp": "2025-01-19T10:30:00Z"
}
```

### Error Handling Strategy

- **Graceful Degradation**: Continue operation when non-critical errors occur
- **Retry Logic**: Implement exponential backoff for transient failures
- **Resource Cleanup**: Ensure proper cleanup on operation failures
- **Client Notification**: Always notify clients of error conditions
- **Detailed Logging**: Log all errors with full context for debugging

## Testing Strategy

### Unit Tests

- Test each component in isolation with mocked dependencies
- Test error conditions and edge cases
- Test data validation and transformation
- Test logging functionality

### Integration Tests

- Test Docker SDK integration with real containers
- Test Unix socket communication
- Test Socket.IO event handling end-to-end
- Test container lifecycle scenarios

### System Tests

- Test complete workflows from client to container
- Test concurrent operations
- Test resource constraints and cleanup
- Test error recovery scenarios

### Test Data Management

- Use Docker test containers for integration tests
- Mock Docker SDK for unit tests
- Create test fixtures for Socket.IO events
- Implement test cleanup procedures

### Performance Tests

- Test container creation/deletion throughput
- Test concurrent socket communication
- Test memory usage under load
- Test response time requirements
