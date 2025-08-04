# Flow Manager

This comprehensive guide provides detailed information about the Flow Manager service, which enables container lifecycle management and communication via Socket.IO.

## Overview

Flow Manager is a WebSocket-based service for managing Docker container lifecycles. It provides real-time container management capabilities including creation, start, stop, restart, update, and deletion operations. The service also facilitates bidirectional communication with containers via Unix sockets.

## Key Features

- **Container Lifecycle Management**: Create, start, stop, restart, update, and delete containers
- **Real-time Communication**: Send and receive messages to/from containers via Unix sockets
- **Status Monitoring**: Monitor container status, health, and resource usage
- **Event-driven Architecture**: Socket.IO events for real-time updates
- **Comprehensive Logging**: Detailed logging of all operations and events

## Documentation Sections

### [API Reference](api_reference.md)

Comprehensive reference for the Flow Manager Socket.IO API, including:

- Event types and formats
- Request and response formats
- Error handling
- Examples for each API endpoint

### [Usage Guide](usage_guide.md)

Practical guide for using the Flow Manager API, including:

- Getting started with the API
- Container lifecycle management examples
- Container communication examples
- Container monitoring examples
- Best practices

### [Error Handling and Troubleshooting](error_handling.md)

Guide for handling errors and troubleshooting issues, including:

- Error response format
- Common error types
- Troubleshooting common issues
- Logging and debugging
- Recovery strategies

### [Deployment and Configuration](deployment_guide.md)

Guide for deploying and configuring the Flow Manager service, including:

- Installation instructions
- Configuration options
- Deployment options (Docker, Kubernetes, etc.)
- Security considerations
- Monitoring and maintenance

## Quick Start

### Installation

```bash
# Using Docker
docker pull kawaflow/flow-manager:latest
docker run -d \
  --name flow-manager \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /tmp/kawaflow/sockets:/tmp/kawaflow/sockets \
  kawaflow/flow-manager:latest

# Using Task Runner
task flow-manager:build
task flow-manager:run
```

### Basic Usage

```javascript
// JavaScript client example
const socket = io("http://localhost:8000");

// Create a container
socket.emit("create_container", {
  image: "flow:latest",
  name: "my-flow-container",
});

// Handle container created event
socket.on("container_created", (data) => {
  console.log("Container created:", data);
  const containerId = data.container_id;

  // Start the container
  socket.emit("start_container", {
    container_id: containerId,
  });
});
```

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/kawaflow/flow-manager) or contact the development team.
