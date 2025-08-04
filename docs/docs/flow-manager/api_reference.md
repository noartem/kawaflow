API Reference

This document provides a comprehensive reference for the Flow Manager Socket.IO API, which enables real-time container lifecycle management and communication.

## Connection

The Flow Manager service exposes a Socket.IO server that clients can connect to for real-time container management.

**Connection URL**: `http://localhost:8000`

### Connection Events

| Event        | Description                                             |
| ------------ | ------------------------------------------------------- |
| `connect`    | Emitted when client successfully connects to the server |
| `disconnect` | Emitted when client disconnects from the server         |

**Example: Connecting to the Socket.IO server**

```javascript
// JavaScript client example
const socket = io("http://localhost:8000");

socket.on("connect", () => {
  console.log("Connected to Flow Manager");
});

socket.on("connected", (data) => {
  console.log("Server welcome message:", data.message);
});

socket.on("disconnect", () => {
  console.log("Disconnected from Flow Manager");
});
```

```python
# Python client example
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to Flow Manager')

@sio.event
def connected(data):
    print('Server welcome message:', data['message'])

@sio.event
def disconnect():
    print('Disconnected from Flow Manager')

sio.connect('http://localhost:8000')
```

## Container Lifecycle Management

### Create Container

Creates a new Docker container with the specified configuration.

**Event**: `create_container`

**Request Format**:

```json
{
  "image": "flow:latest",
  "name": "my-flow-container",
  "environment": {
    "ENV_VAR1": "value1",
    "ENV_VAR2": "value2"
  },
  "volumes": {
    "/host/path": "/container/path"
  },
  "ports": {
    "8080": 8080
  }
}
```

**Response Event**: `container_created`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "name": "my-flow-container",
  "image": "flow:latest",
  "status": "created",
  "socket_path": "/tmp/kawaflow/sockets/my-flow-container.sock",
  "ports": {
    "8080": 8080
  }
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("create_container", {
  image: "flow:latest",
  name: "my-flow-container",
  environment: {
    ENV_VAR1: "value1",
    ENV_VAR2: "value2",
  },
  volumes: {
    "/host/path": "/container/path",
  },
  ports: {
    8080: 8080,
  },
});

socket.on("container_created", (data) => {
  console.log("Container created:", data);
  const containerId = data.container_id;
});
```

```python
# Python client example
sio.emit('create_container', {
    'image': 'flow:latest',
    'name': 'my-flow-container',
    'environment': {
        'ENV_VAR1': 'value1',
        'ENV_VAR2': 'value2'
    },
    'volumes': {
        '/host/path': '/container/path'
    },
    'ports': {
        '8080': 8080
    }
})

@sio.on('container_created')
def on_container_created(data):
    print('Container created:', data)
    container_id = data['container_id']
```

### Start Container

Starts an existing container.

**Event**: `start_container`

**Request Format**:

```json
{
  "container_id": "abc123def456"
}
```

**Response Event**: `container_started`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "status": "running"
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("start_container", {
  container_id: "abc123def456",
});

socket.on("container_started", (data) => {
  console.log("Container started:", data);
});
```

```python
# Python client example
sio.emit('start_container', {
    'container_id': 'abc123def456'
})

@sio.on('container_started')
def on_container_started(data):
    print('Container started:', data)
```

### Stop Container

Stops a running container.

**Event**: `stop_container`

**Request Format**:

```json
{
  "container_id": "abc123def456"
}
```

**Response Event**: `container_stopped`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "status": "stopped"
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("stop_container", {
  container_id: "abc123def456",
});

socket.on("container_stopped", (data) => {
  console.log("Container stopped:", data);
});
```

```python
# Python client example
sio.emit('stop_container', {
    'container_id': 'abc123def456'
})

@sio.on('container_stopped')
def on_container_stopped(data):
    print('Container stopped:', data)
```

### Restart Container

Restarts an existing container.

**Event**: `restart_container`

**Request Format**:

```json
{
  "container_id": "abc123def456"
}
```

**Response Event**: `container_restarted`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "status": "running"
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("restart_container", {
  container_id: "abc123def456",
});

socket.on("container_restarted", (data) => {
  console.log("Container restarted:", data);
});
```

```python
# Python client example
sio.emit('restart_container', {
    'container_id': 'abc123def456'
})

@sio.on('container_restarted')
def on_container_restarted(data):
    print('Container restarted:', data)
```

### Update Container

Updates a container's code without losing container state.

**Event**: `update_container`

**Request Format**:

```json
{
  "container_id": "abc123def456",
  "code_path": "/path/to/new/code"
}
```

**Response Event**: `container_updated`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "code_path": "/path/to/new/code",
  "status": "updated"
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("update_container", {
  container_id: "abc123def456",
  code_path: "/path/to/new/code",
});

socket.on("container_updated", (data) => {
  console.log("Container updated:", data);
});
```

```python
# Python client example
sio.emit('update_container', {
    'container_id': 'abc123def456',
    'code_path': '/path/to/new/code'
})

@sio.on('container_updated')
def on_container_updated(data):
    print('Container updated:', data)
```

### Delete Container

Deletes a container and cleans up associated resources.

**Event**: `delete_container`

**Request Format**:

```json
{
  "container_id": "abc123def456"
}
```

**Response Event**: `container_deleted`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "status": "deleted"
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("delete_container", {
  container_id: "abc123def456",
});

socket.on("container_deleted", (data) => {
  console.log("Container deleted:", data);
});
```

```python
# Python client example
sio.emit('delete_container', {
    'container_id': 'abc123def456'
})

@sio.on('container_deleted')
def on_container_deleted(data):
    print('Container deleted:', data)
```

## Container Communication

### Send Message

Sends a message to a container via Unix socket.

**Event**: `send_message`

**Request Format**:

```json
{
  "container_id": "abc123def456",
  "message": {
    "command": "execute",
    "data": {
      "action": "process",
      "parameters": {
        "input": "sample input"
      }
    }
  }
}
```

**Response Event**: `message_sent`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "message": {
    "command": "execute",
    "data": {
      "action": "process",
      "parameters": {
        "input": "sample input"
      }
    }
  },
  "status": "sent"
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("send_message", {
  container_id: "abc123def456",
  message: {
    command: "execute",
    data: {
      action: "process",
      parameters: {
        input: "sample input",
      },
    },
  },
});

socket.on("message_sent", (data) => {
  console.log("Message sent:", data);
});
```

```python
# Python client example
sio.emit('send_message', {
    'container_id': 'abc123def456',
    'message': {
        'command': 'execute',
        'data': {
            'action': 'process',
            'parameters': {
                'input': 'sample input'
            }
        }
    }
})

@sio.on('message_sent')
def on_message_sent(data):
    print('Message sent:', data)
```

### Receive Message

When a container sends a message, the server emits a `message_received` event to all connected clients.

**Event**: `message_received` (server-initiated)

**Format**:

```json
{
  "container_id": "abc123def456",
  "message": {
    "command": "result",
    "data": {
      "status": "success",
      "result": "processed data"
    }
  },
  "timestamp": "2025-07-21T10:30:00Z"
}
```

**Example**:

```javascript
// JavaScript client example
socket.on("message_received", (data) => {
  console.log("Message received from container:", data);
  const containerId = data.container_id;
  const message = data.message;
});
```

```python
# Python client example
@sio.on('message_received')
def on_message_received(data):
    print('Message received from container:', data)
    container_id = data['container_id']
    message = data['message']
```

## Container Status and Monitoring

### Get Container Status

Retrieves detailed status information for a container.

**Event**: `get_container_status`

**Request Format**:

```json
{
  "container_id": "abc123def456"
}
```

**Response Event**: `container_status`

**Response Format**:

```json
{
  "container_id": "abc123def456",
  "state": "running",
  "health": "healthy",
  "uptime": "0:10:30",
  "socket_connected": true,
  "last_communication": "2025-07-21T10:20:00Z",
  "resource_usage": {
    "cpu_percent": 2.5,
    "memory_usage": 52428800,
    "memory_limit": 2147483648,
    "memory_percent": 2.44,
    "network_rx_bytes": 1024,
    "network_tx_bytes": 2048,
    "disk_read_bytes": 4096,
    "disk_write_bytes": 8192,
    "timestamp": "2025-07-21T10:30:00Z"
  }
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("get_container_status", {
  container_id: "abc123def456",
});

socket.on("container_status", (data) => {
  console.log("Container status:", data);
});
```

```python
# Python client example
sio.emit('get_container_status', {
    'container_id': 'abc123def456'
})

@sio.on('container_status')
def on_container_status(data):
    print('Container status:', data)
```

### List Containers

Lists all managed containers.

**Event**: `list_containers`

**Request Format**:

```json
{}
```

**Response Event**: `container_list`

**Response Format**:

```json
{
  "containers": [
    {
      "id": "abc123def456",
      "name": "flow-container-1",
      "status": "running",
      "image": "flow:latest",
      "created": "2025-07-21T09:00:00Z",
      "socket_path": "/tmp/kawaflow/sockets/flow-container-1.sock",
      "ports": {
        "8080": 8080
      }
    },
    {
      "id": "def456abc789",
      "name": "flow-container-2",
      "status": "stopped",
      "image": "flow:latest",
      "created": "2025-07-21T09:30:00Z",
      "socket_path": "/tmp/kawaflow/sockets/flow-container-2.sock",
      "ports": {
        "8081": 8081
      }
    }
  ],
  "count": 2
}
```

**Example**:

```javascript
// JavaScript client example
socket.emit("list_containers", {});

socket.on("container_list", (data) => {
  console.log("Container list:", data);
  const containers = data.containers;
  const count = data.count;
});
```

```python
# Python client example
sio.emit('list_containers', {})

@sio.on('container_list')
def on_container_list(data):
    print('Container list:', data)
    containers = data['containers']
    count = data['count']
```

### Status Change Notifications

The server automatically emits status change events when container state changes.

**Event**: `status_changed` (server-initiated)

**Format**:

```json
{
  "container_id": "abc123def456",
  "old_state": "running",
  "new_state": "stopped",
  "timestamp": 1721644200.0
}
```

**Example**:

```javascript
// JavaScript client example
socket.on("status_changed", (data) => {
  console.log("Container status changed:", data);
});
```

```python
# Python client example
@sio.on('status_changed')
def on_status_changed(data):
    print('Container status changed:', data)
```

### Container Health Warnings

The server emits health warnings when container health checks fail.

**Event**: `container_health_warning` (server-initiated)

**Format**:

```json
{
  "container_id": "abc123def456",
  "health": "unhealthy",
  "timestamp": 1721644200.0
}
```

**Example**:

```javascript
// JavaScript client example
socket.on("container_health_warning", (data) => {
  console.log("Container health warning:", data);
});
```

```python
# Python client example
@sio.on('container_health_warning')
def on_container_health_warning(data):
    print('Container health warning:', data)
```

### Container Crash Notifications

The server emits crash notifications when containers crash.

**Event**: `container_crashed` (server-initiated)

**Format**:

```json
{
  "container_id": "abc123def456",
  "exit_code": 1,
  "crash_details": {
    "error": "Out of memory",
    "logs": "..."
  },
  "timestamp": 1721644200.0
}
```

**Example**:

```javascript
// JavaScript client example
socket.on("container_crashed", (data) => {
  console.log("Container crashed:", data);
});
```

```python
# Python client example
@sio.on('container_crashed')
def on_container_crashed(data):
    print('Container crashed:', data)
```

### Periodic Status Updates

The server periodically emits status updates for all containers.

**Event**: `container_status_update` (server-initiated)

**Format**:

```json
{
  "container_id": "abc123def456",
  "status": {
    "state": "running",
    "health": "healthy",
    "socket_connected": true,
    "uptime": "0:10:30",
    "resource_usage": {
      "cpu_percent": 2.5,
      "memory_usage": 52428800,
      "memory_limit": 2147483648,
      "memory_percent": 2.44,
      "network_rx_bytes": 1024,
      "network_tx_bytes": 2048,
      "disk_read_bytes": 4096,
      "disk_write_bytes": 8192,
      "timestamp": "2025-07-21T10:30:00Z"
    }
  }
}
```

**Example**:

```javascript
// JavaScript client example
socket.on("container_status_update", (data) => {
  console.log("Container status update:", data);
});
```

```python
# Python client example
@sio.on('container_status_update')
def on_container_status_update(data):
    print('Container status update:', data)
```

## Error Handling

All operations can result in errors. When an error occurs, the server emits an `error` event.

**Event**: `error` (server-initiated)

**Format**:

```json
{
  "error": true,
  "error_type": "docker_api_error",
  "message": "Container not found",
  "details": {
    "operation": "start_container",
    "container_id": "abc123def456"
  },
  "timestamp": "2025-07-21T10:30:00Z"
}
```

### Error Types

| Error Type                | Description                  |
| ------------------------- | ---------------------------- |
| `image_not_found`         | Docker image not found       |
| `container_not_found`     | Container not found          |
| `docker_api_error`        | Docker API error             |
| `socket_error`            | Socket communication error   |
| `socket_timeout_error`    | Socket communication timeout |
| `socket_connection_error` | Socket connection error      |
| `validation_error`        | Invalid request data         |
| `system_error`            | System-level error           |

**Example**:

```javascript
// JavaScript client example
socket.on("error", (data) => {
  console.error("Error:", data);
  const errorType = data.error_type;
  const message = data.message;
  const details = data.details;
});
```

```python
# Python client example
@sio.on('error')
def on_error(data):
    print('Error:', data)
    error_type = data['error_type']
    message = data['message']
    details = data['details']
```

## Activity Logging

The server emits activity log events for user-visible container operations.

**Event**: `activity_log` (server-initiated)

**Format**:

```json
{
  "activity_type": "container_created",
  "container_id": "abc123def456",
  "message": "Container my-flow-container created",
  "details": {
    "name": "my-flow-container",
    "image": "flow:latest"
  },
  "timestamp": "2025-07-21T10:30:00Z"
}
```

### Activity Types

| Activity Type         | Description                     |
| --------------------- | ------------------------------- |
| `container_created`   | Container created               |
| `container_started`   | Container started               |
| `container_stopped`   | Container stopped               |
| `container_restarted` | Container restarted             |
| `container_updated`   | Container code updated          |
| `container_deleted`   | Container deleted               |
| `message_sent`        | Message sent to container       |
| `message_received`    | Message received from container |
| `status_change`       | Container status changed        |
| `health_warning`      | Container health warning        |
| `container_crash`     | Container crashed               |
| `container_error`     | Container operation error       |

**Example**:

```javascript
// JavaScript client example
socket.on("activity_log", (data) => {
  console.log("Activity log:", data);
});
```

```python
# Python client example
@sio.on('activity_log')
def on_activity_log(data):
    print('Activity log:', data)
```
