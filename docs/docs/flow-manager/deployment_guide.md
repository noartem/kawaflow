Deployment and Configuration Guide

This guide provides instructions for deploying and configuring the Flow Manager service in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

Before deploying the Flow Manager service, ensure you have the following prerequisites:

### System Requirements

- **Operating System**: Linux (recommended), Windows, or macOS
- **Python**: Version 3.12 or higher
- **Docker**: Version 20.10 or higher
- **Disk Space**: At least 1GB for the service and container images
- **Memory**: At least 2GB RAM

### Required Software

- **Docker Engine**: For container management
- **Python Dependencies**:
  - FastAPI
  - Socket.IO
  - Docker SDK for Python
  - Uvicorn
  - Pydantic

## Installation

### Using Docker (Recommended)

1. **Pull the Flow Manager Image**:

```bash
docker pull kawaflow/flow-manager:latest
```

2. **Create Socket Directory**:

```bash
mkdir -p /tmp/kawaflow/sockets
chmod 777 /tmp/kawaflow/sockets
```

3. **Run the Container**:

```bash
docker run -d \
  --name flow-manager \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /tmp/kawaflow/sockets:/tmp/kawaflow/sockets \
  kawaflow/flow-manager:latest
```

### Manual Installation

1. **Clone the Repository**:

```bash
git clone https://github.com/kawaflow/flow-manager.git
cd flow-manager
```

2. **Create Virtual Environment**:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**:

```bash
pip install -r requirements.txt
```

4. **Create Socket Directory**:

```bash
mkdir -p /tmp/kawaflow/sockets
chmod 777 /tmp/kawaflow/sockets
```

5. **Run the Service**:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Using Task Runner

The project includes a Taskfile for easy management:

1. **Install Task**:

```bash
# On Windows with Chocolatey
choco install go-task

# On macOS with Homebrew
brew install go-task/tap/go-task

# On Linux
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin
```

2. **Build and Run**:

```bash
# Build the Docker image
task flow-manager:build

# Run the service
task flow-manager:run
```

## Configuration

### Environment Variables

The Flow Manager service can be configured using the following environment variables:

| Variable       | Description                     | Default                 | Example                                     |
| -------------- | ------------------------------- | ----------------------- | ------------------------------------------- |
| `SOCKET_DIR`   | Directory for Unix socket files | `/tmp/kawaflow/sockets` | `/var/run/kawaflow/sockets`                 |
| `LOG_LEVEL`    | Logging level                   | `INFO`                  | `DEBUG`                                     |
| `HOST`         | Host to bind the server         | `0.0.0.0`               | `127.0.0.1`                                 |
| `PORT`         | Port to bind the server         | `8000`                  | `9000`                                      |
| `CORS_ORIGINS` | Allowed CORS origins            | `*`                     | `http://localhost:3000,https://example.com` |

### Configuration File

For more advanced configuration, you can create a `config.json` file:

```json
{
  "socket_dir": "/tmp/kawaflow/sockets",
  "log_level": "INFO",
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "cors_origins": ["*"]
  },
  "docker": {
    "default_image": "flow:latest",
    "network": "kawaflow",
    "volume_driver": "local"
  },
  "monitoring": {
    "health_check_interval": 30,
    "resource_check_interval": 60
  }
}
```

Place this file in the same directory as the Flow Manager service or specify its location using the `CONFIG_FILE` environment variable.

## Deployment Options

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: "3"

services:
  flow-manager:
    image: kawaflow/flow-manager:latest
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/kawaflow/sockets:/tmp/kawaflow/sockets
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

Run with:

```bash
docker-compose up -d
```

### Kubernetes

Create a `flow-manager.yaml` file:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flow-manager
  labels:
    app: flow-manager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flow-manager
  template:
    metadata:
      labels:
        app: flow-manager
    spec:
      containers:
        - name: flow-manager
          image: kawaflow/flow-manager:latest
          ports:
            - containerPort: 8000
          env:
            - name: LOG_LEVEL
              value: "INFO"
          volumeMounts:
            - name: docker-sock
              mountPath: /var/run/docker.sock
            - name: socket-dir
              mountPath: /tmp/kawaflow/sockets
      volumes:
        - name: docker-sock
          hostPath:
            path: /var/run/docker.sock
        - name: socket-dir
          hostPath:
            path: /tmp/kawaflow/sockets
---
apiVersion: v1
kind: Service
metadata:
  name: flow-manager
spec:
  selector:
    app: flow-manager
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

Apply with:

```bash
kubectl apply -f flow-manager.yaml
```

### Systemd Service (Linux)

Create a systemd service file at `/etc/systemd/system/flow-manager.service`:

```ini
[Unit]
Description=Flow Manager Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=<your_user>
WorkingDirectory=/path/to/flow-manager
ExecStart=/path/to/flow-manager/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
Environment=LOG_LEVEL=INFO
Environment=SOCKET_DIR=/tmp/kawaflow/sockets

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable flow-manager
sudo systemctl start flow-manager
```

## Security Considerations

### Docker Socket Security

The Flow Manager service requires access to the Docker socket (`/var/run/docker.sock`) to manage containers. This gives the service significant privileges on the host system. Consider the following security measures:

1. **Run as Non-Root User**:

   - Create a dedicated user for the Flow Manager service
   - Add this user to the `docker` group

2. **Restrict Docker API Access**:

   - Use Docker API authorization plugins
   - Configure Docker daemon to use TLS

3. **Container Isolation**:
   - Use user namespaces for container isolation
   - Apply resource limits to containers

### Network Security

1. **API Access Control**:

   - Configure CORS to restrict access to trusted origins
   - Use a reverse proxy (like Nginx) with authentication

2. **TLS/SSL**:

   - Configure TLS for Socket.IO connections
   - Use a valid SSL certificate

3. **Firewall Rules**:
   - Restrict access to the Flow Manager service port
   - Allow only necessary connections

### Environment Variables

1. **Sensitive Data**:

   - Do not pass sensitive data in environment variables
   - Use secrets management solutions

2. **Default Values**:
   - Change default socket directory in production
   - Use specific CORS origins instead of wildcard (`*`)

## Monitoring and Maintenance

### Health Checks

The Flow Manager service provides a health check endpoint at `/health`:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "flow-manager",
  "socket_dir": "/tmp/kawaflow/sockets",
  "components": {
    "container_manager": "active",
    "socket_handler": "active",
    "event_handler": "active"
  }
}
```

### Logging

Logs are output to stdout/stderr and can be viewed using:

```bash
# Docker
docker logs flow-manager

# Systemd
journalctl -u flow-manager
```

### Backup and Restore

1. **Socket Directory Backup**:

   - Backup the socket directory periodically
   - Include in system backup routines

2. **Container Data Backup**:
   - Use Docker volume backups for container data
   - Implement application-level backup mechanisms

### Upgrading

1. **Docker Image Upgrade**:

```bash
# Pull the latest image
docker pull kawaflow/flow-manager:latest

# Stop and remove the existing container
docker stop flow-manager
docker rm flow-manager

# Run the new container
docker run -d \
  --name flow-manager \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /tmp/kawaflow/sockets:/tmp/kawaflow/sockets \
  kawaflow/flow-manager:latest
```

2. **Manual Upgrade**:

```bash
# Pull the latest code
git pull

# Activate virtual environment
source .venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Restart the service
systemctl restart flow-manager  # If using systemd
# OR
uvicorn main:app --host 0.0.0.0 --port 8000  # If running manually
```
