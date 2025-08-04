Error Handling and Troubleshooting Guide

This guide provides comprehensive information on error handling and troubleshooting for the Flow Manager service.

## Table of Contents

1. [Error Response Format](#error-response-format)
2. [Common Error Types](#common-error-types)
3. [Troubleshooting Common Issues](#troubleshooting-common-issues)
4. [Logging and Debugging](#logging-and-debugging)
5. [Recovery Strategies](#recovery-strategies)

## Error Response Format

All errors in the Flow Manager API follow a standardized format:

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

### Fields Explanation

| Field        | Description                                                            |
| ------------ | ---------------------------------------------------------------------- |
| `error`      | Always `true` for error responses                                      |
| `error_type` | Category of the error (see [Common Error Types](#common-error-types))  |
| `message`    | Human-readable error message                                           |
| `details`    | Additional context about the error, including operation and parameters |
| `timestamp`  | Time when the error occurred                                           |

## Common Error Types

### Docker API Errors

| Error Type            | Description              | Common Causes                                | Resolution                                      |
| --------------------- | ------------------------ | -------------------------------------------- | ----------------------------------------------- |
| `image_not_found`     | Docker image not found   | Image name misspelled, image not pulled      | Check image name, pull image with `docker pull` |
| `container_not_found` | Container not found      | Container ID incorrect, container deleted    | Verify container ID, check if container exists  |
| `docker_api_error`    | General Docker API error | Docker daemon not running, permission issues | Check Docker daemon status, verify permissions  |

### Socket Communication Errors

| Error Type                | Description                | Common Causes                          | Resolution                                   |
| ------------------------- | -------------------------- | -------------------------------------- | -------------------------------------------- |
| `socket_error`            | General socket error       | Socket file missing, permission issues | Check socket file exists, verify permissions |
| `socket_timeout_error`    | Socket operation timed out | Container unresponsive, network issues | Check container status, increase timeout     |
| `socket_connection_error` | Socket connection failed   | Socket file missing, container crashed | Check socket file, restart container         |

### Validation Errors

| Error Type         | Description          | Common Causes                           | Resolution                                        |
| ------------------ | -------------------- | --------------------------------------- | ------------------------------------------------- |
| `validation_error` | Invalid request data | Missing required fields, invalid format | Check request format, provide all required fields |

### System Errors

| Error Type     | Description        | Common Causes                                  | Resolution                              |
| -------------- | ------------------ | ---------------------------------------------- | --------------------------------------- |
| `system_error` | System-level error | Disk space, memory constraints, network issues | Check system resources, restart service |

## Troubleshooting Common Issues

### Container Creation Issues

#### Container Creation Fails with "Image Not Found"

**Symptoms**:

- Error response with `error_type: "image_not_found"`
- Container creation fails

**Possible Causes**:

1. Image name is misspelled
2. Image has not been pulled
3. Image repository requires authentication

**Resolution Steps**:

1. Verify image name and tag
2. Pull the image manually: `docker pull <image_name>`
3. Check Docker registry authentication

#### Container Creation Fails with "Port Already Allocated"

**Symptoms**:

- Error response with `error_type: "docker_api_error"`
- Error message contains "port is already allocated"

**Possible Causes**:

1. Port is already in use by another container or process
2. Previous container was not properly cleaned up

**Resolution Steps**:

1. Check for processes using the port: `netstat -ano | findstr <port>`
2. Use a different port
3. Stop the process using the port

### Container Operation Issues

#### Container Start Fails

**Symptoms**:

- Error response when starting container
- Container remains in "created" state

**Possible Causes**:

1. Container configuration issues
2. Resource constraints
3. Volume mount issues

**Resolution Steps**:

1. Check container logs: `docker logs <container_id>`
2. Verify volume mounts and permissions
3. Check system resources (memory, disk space)

#### Container Update Fails

**Symptoms**:

- Error response when updating container
- Container state may be inconsistent

**Possible Causes**:

1. Code path does not exist
2. Permission issues with code path
3. Container is in an invalid state

**Resolution Steps**:

1. Verify code path exists
2. Check permissions on code path
3. Ensure container is in a valid state (running or stopped)

### Socket Communication Issues

#### Socket Connection Fails

**Symptoms**:

- Error response with `error_type: "socket_connection_error"`
- Cannot send or receive messages

**Possible Causes**:

1. Socket file does not exist
2. Permission issues with socket file
3. Container crashed or is not running

**Resolution Steps**:

1. Check if socket file exists: `ls -la /tmp/kawaflow/sockets/`
2. Verify socket file permissions
3. Check container status: `docker ps -a`

#### Socket Communication Timeouts

**Symptoms**:

- Error response with `error_type: "socket_timeout_error"`
- Operations take a long time and then fail

**Possible Causes**:

1. Container is unresponsive
2. Container is processing a long-running operation
3. Network issues

**Resolution Steps**:

1. Check container resource usage
2. Increase timeout value for operations
3. Restart container if unresponsive

## Logging and Debugging

### System Logs

The Flow Manager service uses structured logging with different log levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning events that might cause issues
- **ERROR**: Error events that might still allow the service to continue
- **CRITICAL**: Critical events that prevent the service from working

### Accessing Logs

#### Container Logs

To view logs for a specific container:

```bash
docker logs <container_id>
```

#### Flow Manager Logs

To view Flow Manager service logs:

```bash
# If running in Docker
docker logs flow-manager

# If running locally
tail -f flow-manager.log
```

### Debug Mode

To enable debug logging, set the `LOG_LEVEL` environment variable to `DEBUG`:

```bash
# In Docker
docker run -e LOG_LEVEL=DEBUG flow-manager

# In local environment
export LOG_LEVEL=DEBUG
python main.py
```

### Common Log Patterns

#### Container Lifecycle Events

```
[INFO] Container operation: create, container_id=abc123def456, name=my-flow-container
[INFO] Container operation: start, container_id=abc123def456, status=started
```

#### Socket Communication

```
[DEBUG] Socket communication: sent, container_id=abc123def456, message={"command": "execute", "data": {...}}
[DEBUG] Socket communication: received, container_id=abc123def456, message={"command": "result", "data": {...}}
```

#### Error Logs

```
[ERROR] Operation: start_container, container_id=abc123def456, error=Container not found
[ERROR] Operation: send_message, container_id=abc123def456, error=Socket connection failed
```

## Recovery Strategies

### Automatic Recovery

The Flow Manager service implements several automatic recovery mechanisms:

1. **Container Crash Recovery**:

   - Detects container crashes
   - Emits `container_crashed` event
   - Optionally restarts crashed containers

2. **Socket Reconnection**:

   - Detects socket disconnections
   - Attempts to reconnect sockets
   - Emits `socket_connected` event when reconnected

3. **Transient Error Retry**:
   - Implements exponential backoff for transient errors
   - Retries operations with increasing delays
   - Gives up after maximum retry attempts

### Manual Recovery

#### Recovering from Container Failures

1. **Restart Container**:

   ```javascript
   socket.emit("restart_container", { container_id: "abc123def456" });
   ```

2. **Recreate Container**:

   ```javascript
   // First delete the failed container
   socket.emit("delete_container", { container_id: "abc123def456" });

   // Then create a new container
   socket.emit("create_container", {
     image: "flow:latest",
     name: "my-flow-container",
     // other configuration...
   });
   ```

#### Recovering from Socket Communication Issues

1. **Clean Up Socket**:

   ```bash
   # Remove socket file manually if needed
   rm /tmp/kawaflow/sockets/container_name.sock
   ```

2. **Restart Flow Manager Service**:

   ```bash
   # If running in Docker
   docker restart flow-manager

   # If running locally
   systemctl restart flow-manager
   ```

### Preventive Measures

1. **Regular Health Checks**:

   - Periodically check container health
   - Monitor resource usage
   - Set up alerts for warning thresholds

2. **Graceful Shutdown**:

   - Always use proper shutdown procedures
   - Allow containers to clean up resources
   - Preserve state when possible

3. **Backup and Restore**:
   - Regularly backup container data
   - Implement restore procedures
   - Test recovery processes
