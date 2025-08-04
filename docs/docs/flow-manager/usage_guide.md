Usage Guide

This guide provides practical examples for using the Flow Manager API to manage container lifecycles and communicate with containers.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Container Lifecycle Management](#container-lifecycle-management)
3. [Container Communication](#container-communication)
4. [Container Monitoring](#container-monitoring)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

## Getting Started

### Installation

Before using the Flow Manager API, ensure you have the necessary dependencies installed:

**JavaScript Client**:

```bash
npm install socket.io-client
```

**Python Client**:

```bash
pip install python-socketio
```

### Connecting to the Flow Manager

**JavaScript Example**:

```javascript
const io = require("socket.io-client");

// Connect to the Flow Manager server
const socket = io("http://localhost:8000");

// Handle connection events
socket.on("connect", () => {
  console.log("Connected to Flow Manager");
});

socket.on("connected", (data) => {
  console.log("Server welcome message:", data.message);
});

socket.on("disconnect", () => {
  console.log("Disconnected from Flow Manager");
});

// Handle errors
socket.on("error", (data) => {
  console.error("Error:", data.error_type, data.message);
});

// Handle activity logs
socket.on("activity_log", (data) => {
  console.log("Activity:", data.activity_type, data.message);
});
```

**Python Example**:

```python
import socketio

# Create Socket.IO client
sio = socketio.Client()

# Handle connection events
@sio.event
def connect():
    print('Connected to Flow Manager')

@sio.event
def connected(data):
    print('Server welcome message:', data['message'])

@sio.event
def disconnect():
    print('Disconnected from Flow Manager')

# Handle errors
@sio.on('error')
def on_error(data):
    print('Error:', data['error_type'], data['message'])

# Handle activity logs
@sio.on('activity_log')
def on_activity_log(data):
    print('Activity:', data['activity_type'], data['message'])

# Connect to the Flow Manager server
sio.connect('http://localhost:8000')
```

## Container Lifecycle Management

### Complete Container Lifecycle Example

This example demonstrates a complete container lifecycle from creation to deletion.

**JavaScript Example**:

```javascript
// Create a container
function createContainer() {
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
}

// Start a container
function startContainer(containerId) {
  socket.emit("start_container", {
    container_id: containerId,
  });
}

// Stop a container
function stopContainer(containerId) {
  socket.emit("stop_container", {
    container_id: containerId,
  });
}

// Restart a container
function restartContainer(containerId) {
  socket.emit("restart_container", {
    container_id: containerId,
  });
}

// Update a container
function updateContainer(containerId, codePath) {
  socket.emit("update_container", {
    container_id: containerId,
    code_path: codePath,
  });
}

// Delete a container
function deleteContainer(containerId) {
  socket.emit("delete_container", {
    container_id: containerId,
  });
}

// Handle container events
socket.on("container_created", (data) => {
  console.log("Container created:", data);
  const containerId = data.container_id;

  // Start the container after creation
  startContainer(containerId);
});

socket.on("container_started", (data) => {
  console.log("Container started:", data);
  const containerId = data.container_id;

  // Example: Update the container after starting
  // updateContainer(containerId, '/path/to/new/code');
});

socket.on("container_stopped", (data) => {
  console.log("Container stopped:", data);
});

socket.on("container_restarted", (data) => {
  console.log("Container restarted:", data);
});

socket.on("container_updated", (data) => {
  console.log("Container updated:", data);
});

socket.on("container_deleted", (data) => {
  console.log("Container deleted:", data);
});

// Start the lifecycle
createContainer();
```

**Python Example**:

```python
import time

# Create a container
def create_container():
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

# Start a container
def start_container(container_id):
    sio.emit('start_container', {
        'container_id': container_id
    })

# Stop a container
def stop_container(container_id):
    sio.emit('stop_container', {
        'container_id': container_id
    })

# Restart a container
def restart_container(container_id):
    sio.emit('restart_container', {
        'container_id': container_id
    })

# Update a container
def update_container(container_id, code_path):
    sio.emit('update_container', {
        'container_id': container_id,
        'code_path': code_path
    })

# Delete a container
def delete_container(container_id):
    sio.emit('delete_container', {
        'container_id': container_id
    })

# Handle container events
@sio.on('container_created')
def on_container_created(data):
    print('Container created:', data)
    container_id = data['container_id']

    # Start the container after creation
    start_container(container_id)

@sio.on('container_started')
def on_container_started(data):
    print('Container started:', data)
    container_id = data['container_id']

    # Example: Update the container after starting
    # update_container(container_id, '/path/to/new/code')

@sio.on('container_stopped')
def on_container_stopped(data):
    print('Container stopped:', data)

@sio.on('container_restarted')
def on_container_restarted(data):
    print('Container restarted:', data)

@sio.on('container_updated')
def on_container_updated(data):
    print('Container updated:', data)

@sio.on('container_deleted')
def on_container_deleted(data):
    print('Container deleted:', data)

# Start the lifecycle
create_container()
```

## Container Communication

### Sending and Receiving Messages

This example demonstrates how to send messages to containers and handle responses.

**JavaScript Example**:

```javascript
// Send a message to a container
function sendMessage(containerId, command, data) {
  socket.emit("send_message", {
    container_id: containerId,
    message: {
      command: command,
      data: data,
    },
  });
}

// Handle message events
socket.on("message_sent", (data) => {
  console.log("Message sent:", data);
});

socket.on("message_received", (data) => {
  console.log("Message received from container:", data);
  const containerId = data.container_id;
  const message = data.message;

  // Process the message based on command
  if (message.command === "result") {
    console.log("Result received:", message.data);
  } else if (message.command === "status") {
    console.log("Status update:", message.data);
  } else if (message.command === "error") {
    console.error("Container error:", message.data);
  }
});

// Example usage
function processData(containerId, inputData) {
  sendMessage(containerId, "process", {
    input: inputData,
    options: {
      format: "json",
      validate: true,
    },
  });
}

// Call this function when you want to process data
// processData('abc123def456', 'sample input data');
```

**Python Example**:

```python
# Send a message to a container
def send_message(container_id, command, data):
    sio.emit('send_message', {
        'container_id': container_id,
        'message': {
            'command': command,
            'data': data
        }
    })

# Handle message events
@sio.on('message_sent')
def on_message_sent(data):
    print('Message sent:', data)

@sio.on('message_received')
def on_message_received(data):
    print('Message received from container:', data)
    container_id = data['container_id']
    message = data['message']

    # Process the message based on command
    if message['command'] == 'result':
        print('Result received:', message['data'])
    elif message['command'] == 'status':
        print('Status update:', message['data'])
    elif message['command'] == 'error':
        print('Container error:', message['data'])

# Example usage
def process_data(container_id, input_data):
    send_message(container_id, 'process', {
        'input': input_data,
        'options': {
            'format': 'json',
            'validate': True
        }
    })

# Call this function when you want to process data
# process_data('abc123def456', 'sample input data')
```

## Container Monitoring

### Monitoring Container Status

This example demonstrates how to monitor container status and handle status changes.

**JavaScript Example**:

```javascript
// Get container status
function getContainerStatus(containerId) {
  socket.emit("get_container_status", {
    container_id: containerId,
  });
}

// List all containers
function listContainers() {
  socket.emit("list_containers", {});
}

// Handle status events
socket.on("container_status", (data) => {
  console.log("Container status:", data);

  // Check container health
  if (data.health === "unhealthy") {
    console.warn("Container is unhealthy:", data.container_id);
  }

  // Check resource usage
  const resourceUsage = data.resource_usage;
  if (resourceUsage.cpu_percent > 80) {
    console.warn("High CPU usage:", resourceUsage.cpu_percent + "%");
  }
  if (resourceUsage.memory_percent > 80) {
    console.warn("High memory usage:", resourceUsage.memory_percent + "%");
  }
});

socket.on("container_list", (data) => {
  console.log("Container list:", data);

  // Process each container
  data.containers.forEach((container) => {
    console.log(
      `Container ${container.name} (${container.id}): ${container.status}`
    );

    // Get detailed status for each container
    getContainerStatus(container.id);
  });
});

// Handle automatic status updates
socket.on("status_changed", (data) => {
  console.log("Container status changed:", data);

  // Get updated status when state changes
  getContainerStatus(data.container_id);
});

socket.on("container_health_warning", (data) => {
  console.warn("Container health warning:", data);
});

socket.on("container_crashed", (data) => {
  console.error("Container crashed:", data);

  // Example: Restart the container after crash
  // restartContainer(data.container_id);
});

socket.on("container_status_update", (data) => {
  console.log("Container status update:", data);
});

// Start monitoring
listContainers();
```

**Python Example**:

```python
# Get container status
def get_container_status(container_id):
    sio.emit('get_container_status', {
        'container_id': container_id
    })

# List all containers
def list_containers():
    sio.emit('list_containers', {})

# Handle status events
@sio.on('container_status')
def on_container_status(data):
    print('Container status:', data)

    # Check container health
    if data['health'] == 'unhealthy':
        print('Container is unhealthy:', data['container_id'])

    # Check resource usage
    resource_usage = data['resource_usage']
    if resource_usage['cpu_percent'] > 80:
        print('High CPU usage:', resource_usage['cpu_percent'], '%')
    if resource_usage['memory_percent'] > 80:
        print('High memory usage:', resource_usage['memory_percent'], '%')

@sio.on('container_list')
def on_container_list(data):
    print('Container list:', data)

    # Process each container
    for container in data['containers']:
        print(f"Container {container['name']} ({container['id']}): {container['status']}")

        # Get detailed status for each container
        get_container_status(container['id'])

# Handle automatic status updates
@sio.on('status_changed')
def on_status_changed(data):
    print('Container status changed:', data)

    # Get updated status when state changes
    get_container_status(data['container_id'])

@sio.on('container_health_warning')
def on_container_health_warning(data):
    print('Container health warning:', data)

@sio.on('container_crashed')
def on_container_crashed(data):
    print('Container crashed:', data)

    # Example: Restart the container after crash
    # restart_container(data['container_id'])

@sio.on('container_status_update')
def on_container_status_update(data):
    print('Container status update:', data)

# Start monitoring
list_containers()
```

## Error Handling

### Comprehensive Error Handling

This example demonstrates comprehensive error handling for all container operations.

**JavaScript Example**:

```javascript
// Error handling function
function handleError(error) {
  console.error(`Error (${error.error_type}): ${error.message}`);

  switch (error.error_type) {
    case "image_not_found":
      console.error(
        "The specified Docker image was not found. Please check the image name and ensure it exists."
      );
      break;

    case "container_not_found":
      console.error(
        "The specified container was not found. It may have been deleted or never existed."
      );
      break;

    case "docker_api_error":
      console.error(
        "Docker API error occurred. Check Docker daemon status and permissions."
      );
      break;

    case "socket_error":
    case "socket_timeout_error":
    case "socket_connection_error":
      console.error(
        "Socket communication error. The container may be unresponsive or the socket file may be missing."
      );
      break;

    case "validation_error":
      console.error(
        "Invalid request data. Please check the request format and required fields."
      );
      break;

    case "system_error":
      console.error(
        "System-level error occurred. Check system resources and permissions."
      );
      break;

    default:
      console.error("Unknown error occurred.");
  }

  // Log error details
  if (error.details) {
    console.error("Error details:", error.details);
  }

  // Implement recovery strategies based on error type
  if (
    error.error_type === "container_not_found" &&
    error.details &&
    error.details.operation === "start_container"
  ) {
    console.log("Attempting to recreate the missing container...");
    // Implement recreation logic here
  }

  if (error.error_type === "socket_connection_error") {
    console.log("Attempting to reconnect socket...");
    // Implement reconnection logic here
  }
}

// Register error handler
socket.on("error", handleError);

// Example of try-catch pattern for client-side errors
async function safeContainerOperation(operation, params) {
  try {
    return await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Operation timed out"));
      }, 30000); // 30 second timeout

      const eventName = operation.replace("_", "_");
      socket.once(eventName, (data) => {
        clearTimeout(timeout);
        resolve(data);
      });

      socket.once("error", (error) => {
        if (error.details && error.details.operation === operation) {
          clearTimeout(timeout);
          reject(error);
        }
      });

      socket.emit(operation, params);
    });
  } catch (error) {
    handleError(error);
    throw error; // Re-throw for caller handling
  }
}

// Example usage
async function startContainerSafely(containerId) {
  try {
    const result = await safeContainerOperation("start_container", {
      container_id: containerId,
    });
    console.log("Container started successfully:", result);
    return result;
  } catch (error) {
    console.error("Failed to start container:", containerId);
    return null;
  }
}
```

**Python Example**:

```python
# Error handling function
def handle_error(error):
    print(f"Error ({error['error_type']}): {error['message']}")

    if error['error_type'] == 'image_not_found':
        print('The specified Docker image was not found. Please check the image name and ensure it exists.')

    elif error['error_type'] == 'container_not_found':
        print('The specified container was not found. It may have been deleted or never existed.')

    elif error['error_type'] == 'docker_api_error':
        print('Docker API error occurred. Check Docker daemon status and permissions.')

    elif error['error_type'] in ['socket_error', 'socket_timeout_error', 'socket_connection_error']:
        print('Socket communication error. The container may be unresponsive or the socket file may be missing.')

    elif error['error_type'] == 'validation_error':
        print('Invalid request data. Please check the request format and required fields.')

    elif error['error_type'] == 'system_error':
        print('System-level error occurred. Check system resources and permissions.')

    else:
        print('Unknown error occurred.')

    # Log error details
    if 'details' in error:
        print('Error details:', error['details'])

    # Implement recovery strategies based on error type
    if error['error_type'] == 'container_not_found' and 'details' in error and error['details'].get('operation') == 'start_container':
        print('Attempting to recreate the missing container...')
        # Implement recreation logic here

    if error['error_type'] == 'socket_connection_error':
        print('Attempting to reconnect socket...')
        # Implement reconnection logic here

# Register error handler
@sio.on('error')
def on_error(error):
    handle_error(error)

# Example of safe operation pattern
import asyncio
from functools import partial

async def safe_container_operation(operation, params):
    try:
        future = asyncio.get_event_loop().create_future()

        # Set timeout
        timeout_task = asyncio.create_task(asyncio.sleep(30))  # 30 second timeout

        # Success callback
        event_name = operation.replace('_', '_')
        def on_success(data):
            if not future.done():
                future.set_result(data)

        # Error callback
        def on_error(error):
            if error.get('details', {}).get('operation') == operation and not future.done():
                future.set_exception(Exception(f"{error['error_type']}: {error['message']}"))

        # Register callbacks
        sio.on(event_name, on_success)
        sio.on('error', on_error)

        # Emit event
        sio.emit(operation, params)

        # Wait for result or timeout
        done, pending = await asyncio.wait(
            [future, timeout_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Clean up
        for task in pending:
            task.cancel()

        # Remove listeners
        sio.off(event_name, on_success)
        sio.off('error', on_error)

        # Check if timed out
        if timeout_task in done:
            raise Exception('Operation timed out')

        # Return result
        return future.result()

    except Exception as e:
        print(f"Error in {operation}:", str(e))
        raise

# Example usage
async def start_container_safely(container_id):
    try:
        result = await safe_container_operation('start_container', {'container_id': container_id})
        print('Container started successfully:', result)
        return result
    except Exception as e:
        print('Failed to start container:', container_id)
        return None
```

## Best Practices

### Container Lifecycle Management

1. **Container Naming**:

   - Use descriptive names for containers to easily identify their purpose
   - Include version or timestamp in names for tracking

2. **Resource Management**:

   - Always clean up unused containers to free resources
   - Monitor resource usage and set appropriate limits

3. **Error Recovery**:
   - Implement automatic restart for crashed containers
   - Use exponential backoff for retry attempts

### Container Communication

1. **Message Structure**:

   - Use consistent message formats with command and data fields
   - Include message IDs for tracking requests and responses

2. **Timeout Handling**:

   - Set appropriate timeouts for message operations
   - Implement retry logic for transient failures

3. **Error Handling**:
   - Handle socket communication errors gracefully
   - Log detailed error information for debugging

### Container Monitoring

1. **Proactive Monitoring**:

   - Regularly check container health and resource usage
   - Set up alerts for resource thresholds

2. **Logging**:

   - Log all container operations for audit trails
   - Include timestamps and container IDs in logs

3. **Status Tracking**:
   - Track container state transitions
   - Maintain history of status changes

### Security

1. **Environment Variables**:

   - Avoid storing sensitive information in environment variables
   - Use secure methods for passing credentials

2. **Volume Mounts**:

   - Restrict volume mounts to necessary directories only
   - Use read-only mounts when possible

3. **Network Security**:
   - Limit exposed ports to necessary services only
   - Use secure communication channels

### Performance

1. **Batch Operations**:

   - Group related operations to reduce overhead
   - Use bulk status updates when possible

2. **Connection Management**:

   - Reuse connections when possible
   - Implement connection pooling for multiple clients

3. **Resource Optimization**:
   - Use lightweight container images
   - Optimize code for resource efficiency
