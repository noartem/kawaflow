"""
Container lifecycle management using Docker SDK.

This module provides the ContainerManager class for managing Docker containers
throughout their lifecycle, including creation, start/stop operations, updates,
and cleanup with Unix socket integration.
"""

import asyncio
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

import docker
from docker.errors import APIError, ImageNotFound, NotFound

from models import (
    ContainerConfig,
    ContainerHealth,
    ContainerInfo,
    ContainerState,
    ContainerStatus,
    HealthCheckConfig,
    HealthCheckResult,
    HealthCheckType,
    HealthStatusHistory,
)
from system_logger import SystemLogger


class ContainerManager:
    """
    Manages Docker container lifecycle operations.

    Provides comprehensive container management including creation with Unix socket
    mounting, start/stop/restart operations, code updates, and proper cleanup.
    """

    def __init__(self, socket_dir: str = "/tmp/kawaflow/sockets"):
        """
        Initialize ContainerManager.

        Args:
            socket_dir: Directory for Unix socket files
        """
        self.docker_client = docker.from_env()
        self.socket_dir = socket_dir
        self.logger = SystemLogger()

        # Ensure socket directory exists
        os.makedirs(self.socket_dir, exist_ok=True)

        # Container monitoring state
        self._container_states: Dict[str, ContainerState] = {}
        self._status_change_callbacks: List[Callable] = []
        self._health_check_callbacks: List[Callable] = []
        self._crash_callbacks: List[Callable] = []
        self._resource_alert_callbacks: List[Callable] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_active = False

        # Resource usage monitoring
        self._resource_usage_history: Dict[str, List[Dict[str, Any]]] = {}
        self._resource_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_read_bytes_per_sec": 100 * 1024 * 1024,  # 100MB/s
            "disk_write_bytes_per_sec": 100 * 1024 * 1024,  # 100MB/s
            "network_rx_bytes_per_sec": 50 * 1024 * 1024,  # 50MB/s
            "network_tx_bytes_per_sec": 50 * 1024 * 1024,  # 50MB/s
        }
        self._resource_monitoring_enabled = True

        # Enhanced health check system
        self._health_check_configs: Dict[str, "HealthCheckConfig"] = {}
        self._health_status_history: Dict[str, "HealthStatusHistory"] = {}
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
        self._default_health_config = None  # Will be imported after models

        self.logger.log_debug(
            "ContainerManager initialized", {"socket_dir": self.socket_dir}
        )

    async def create_container(self, config: ContainerConfig) -> ContainerInfo:
        """
        Create a new Docker container with Unix socket mounting.

        Args:
            config: Container configuration

        Returns:
            ContainerInfo: Information about the created container

        Raises:
            ImageNotFound: If the specified image is not available
            APIError: If container creation fails
        """
        try:
            self.logger.log_debug(
                "Creating container", {"image": config.image, "name": config.name}
            )

            # Generate container ID for socket naming
            container_name = (
                config.name or f"flow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
            socket_path = os.path.join(self.socket_dir, f"{container_name}.sock")

            # Prepare port bindings
            port_bindings = {}
            exposed_ports = {}
            for container_port, host_port in config.ports.items():
                port_key = f"{container_port}/tcp"
                exposed_ports[port_key] = {}
                port_bindings[port_key] = host_port

            # Prepare bind mounts
            binds = []
            for host_path, container_path in config.volumes.items():
                binds.append(f"{host_path}:{container_path}")
            # Add socket bind
            binds.append(f"{socket_path}:/var/run/kawaflow.sock")

            # Create container
            container = self.docker_client.containers.create(
                image=config.image,
                name=container_name,
                environment=config.environment,
                ports=exposed_ports,
                host_config=self.docker_client.api.create_host_config(
                    port_bindings=port_bindings,
                    binds=binds,
                ),
                command=config.command,
                working_dir=config.working_dir,
                detach=True,
            )

            # Create container info
            container_info = self._build_container_info(container, socket_path)

            self.logger.log_container_operation(
                "create",
                container.id,
                {
                    "name": container_name,
                    "image": config.image,
                    "socket_path": socket_path,
                },
            )

            return container_info

        except ImageNotFound as e:
            self.logger.log_error(
                e, {"operation": "create_container", "image": config.image}
            )
            raise
        except APIError as e:
            self.logger.log_error(
                e, {"operation": "create_container", "config": config.dict()}
            )
            raise

    async def start_container(self, container_id: str) -> None:
        """
        Start a container.

        Args:
            container_id: ID of the container to start

        Raises:
            NotFound: If container doesn't exist
            APIError: If start operation fails
        """
        try:
            self.logger.log_debug("Starting container", {"container_id": container_id})

            container = self.docker_client.containers.get(container_id)
            container.start()

            self.logger.log_container_operation(
                "start", container_id, {"status": "started"}
            )

        except NotFound as e:
            self.logger.log_error(
                e, {"operation": "start_container", "container_id": container_id}
            )
            raise
        except APIError as e:
            self.logger.log_error(
                e, {"operation": "start_container", "container_id": container_id}
            )
            raise

    async def stop_container(self, container_id: str) -> None:
        """
        Stop a container gracefully.

        Args:
            container_id: ID of the container to stop

        Raises:
            NotFound: If container doesn't exist
            APIError: If stop operation fails
        """
        try:
            self.logger.log_debug("Stopping container", {"container_id": container_id})

            container = self.docker_client.containers.get(container_id)
            container.stop()

            self.logger.log_container_operation(
                "stop", container_id, {"status": "stopped"}
            )

        except NotFound as e:
            self.logger.log_error(
                e, {"operation": "stop_container", "container_id": container_id}
            )
            raise
        except APIError as e:
            self.logger.log_error(
                e, {"operation": "stop_container", "container_id": container_id}
            )
            raise

    async def restart_container(self, container_id: str) -> None:
        """
        Restart a container.

        Args:
            container_id: ID of the container to restart

        Raises:
            NotFound: If container doesn't exist
            APIError: If restart operation fails
        """
        try:
            self.logger.log_debug(
                "Restarting container", {"container_id": container_id}
            )

            container = self.docker_client.containers.get(container_id)
            container.restart()

            self.logger.log_container_operation(
                "restart", container_id, {"status": "restarted"}
            )

        except NotFound as e:
            self.logger.log_error(
                e, {"operation": "restart_container", "container_id": container_id}
            )
            raise
        except APIError as e:
            self.logger.log_error(
                e, {"operation": "restart_container", "container_id": container_id}
            )
            raise

    async def update_container(self, container_id: str, code_path: str) -> None:
        """
        Update container code with proper volume mounting and rollback capability.

        This method implements a comprehensive container update process that:
        1. Updates the container's code volume with new code
        2. Preserves the existing Unix socket connection
        3. Restarts the container if it was running
        4. Provides rollback capability on update failure

        Args:
            container_id: ID of the container to update
            code_path: Path to new code to deploy

        Raises:
            NotFound: If container doesn't exist
            APIError: If update operation fails
            FileNotFoundError: If code path doesn't exist
        """
        backup_path = None
        container = None
        original_state = None

        try:
            self.logger.log_debug(
                "Starting container update",
                {"container_id": container_id, "code_path": code_path},
            )

            # Validate code path exists
            if not os.path.exists(code_path):
                raise FileNotFoundError(f"Code path not found: {code_path}")

            # Get container and preserve original state
            container = self.docker_client.containers.get(container_id)
            container.reload()  # Ensure we have latest state
            original_state = container.status
            was_running = original_state == "running"

            self.logger.log_debug(
                "Container state captured",
                {"container_id": container_id, "original_state": original_state},
            )

            # Get container configuration for volume mounting
            container_config = container.attrs.get("Config", {})
            host_config = container.attrs.get("HostConfig", {})
            binds = host_config.get("Binds", [])

            # Find existing code volume mount (if any)
            code_volume_mount = None
            socket_volume_mount = None
            other_mounts = []

            for bind in binds:
                if ":/var/run/kawaflow.sock" in bind:
                    socket_volume_mount = bind
                elif ":/app" in bind or ":/code" in bind:
                    code_volume_mount = bind
                else:
                    other_mounts.append(bind)

            # Create backup of existing code volume if it exists
            if code_volume_mount:
                host_code_path = code_volume_mount.split(":")[0]
                if os.path.exists(host_code_path):
                    backup_path = f"{host_code_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copytree(host_code_path, backup_path)
                    self.logger.log_debug(
                        "Created code backup",
                        {"backup_path": backup_path, "original_path": host_code_path},
                    )

            # Create new code volume directory
            code_volume_dir = os.path.join(self.socket_dir, f"{container.name}_code")
            os.makedirs(code_volume_dir, exist_ok=True)

            # Copy new code to volume directory
            # Clear existing code first
            if os.path.exists(code_volume_dir):
                for item in os.listdir(code_volume_dir):
                    item_path = os.path.join(code_volume_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)

            # Copy new code
            for item in os.listdir(code_path):
                src_path = os.path.join(code_path, item)
                dst_path = os.path.join(code_volume_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)

            self.logger.log_debug(
                "Code copied to volume",
                {"code_volume_dir": code_volume_dir, "source": code_path},
            )

            # Stop container if running (preserving socket)
            if was_running:
                self.logger.log_debug(
                    "Stopping container for update", {"container_id": container_id}
                )
                container.stop()

            # Create new container with updated code volume
            # Preserve all original configuration but update code mount
            new_binds = other_mounts.copy()

            # Add socket mount (preserve existing socket connection)
            if socket_volume_mount:
                new_binds.append(socket_volume_mount)
            else:
                # Create socket mount if it doesn't exist
                socket_path = os.path.join(self.socket_dir, f"{container.name}.sock")
                new_binds.append(f"{socket_path}:/var/run/kawaflow.sock")

            # Add updated code mount
            new_binds.append(f"{code_volume_dir}:/app")

            # Get original container configuration
            image = container.image.id
            name = container.name
            environment = container_config.get("Env", [])
            ports = container_config.get("ExposedPorts", {})
            command = container_config.get("Cmd")
            working_dir = container_config.get("WorkingDir")

            # Parse port bindings
            port_bindings = {}
            network_settings = container.attrs.get("NetworkSettings", {})
            original_ports = network_settings.get("Ports", {})
            for container_port, host_bindings in original_ports.items():
                if host_bindings:
                    port_bindings[container_port] = host_bindings[0].get("HostPort")

            # Remove old container
            container.remove()

            self.logger.log_debug(
                "Creating updated container",
                {"name": name, "image": image, "binds": new_binds},
            )

            # Create new container with updated configuration
            new_container = self.docker_client.containers.create(
                image=image,
                name=name,
                environment=environment,
                ports=ports,
                host_config=self.docker_client.api.create_host_config(
                    port_bindings=port_bindings,
                    binds=new_binds,
                ),
                command=command,
                working_dir=working_dir,
                detach=True,
            )

            # Start container if it was originally running
            if was_running:
                self.logger.log_debug(
                    "Starting updated container", {"container_id": new_container.id}
                )
                new_container.start()

            # Clean up backup if update was successful
            if backup_path and os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                self.logger.log_debug("Cleaned up backup", {"backup_path": backup_path})

            self.logger.log_container_operation(
                "update",
                new_container.id,
                {
                    "code_path": code_path,
                    "was_running": was_running,
                    "original_container": container_id,
                    "new_container": new_container.id,
                    "status": "updated",
                },
            )

        except Exception as e:
            # Rollback on failure
            self.logger.log_error(
                e,
                {
                    "operation": "update_container",
                    "container_id": container_id,
                    "code_path": code_path,
                    "rollback_initiated": True,
                },
            )

            # Attempt rollback if we have backup
            if backup_path and os.path.exists(backup_path):
                try:
                    self.logger.log_debug(
                        "Initiating rollback", {"backup_path": backup_path}
                    )

                    # If we created a new container but it failed, try to restore original
                    if container and original_state:
                        # Try to restore from backup
                        if code_volume_mount:
                            host_code_path = code_volume_mount.split(":")[0]
                            if os.path.exists(host_code_path):
                                shutil.rmtree(host_code_path)
                            shutil.copytree(backup_path, host_code_path)

                        self.logger.log_debug(
                            "Rollback completed", {"backup_path": backup_path}
                        )

                except Exception as rollback_error:
                    self.logger.log_error(
                        rollback_error,
                        {
                            "operation": "rollback_container_update",
                            "container_id": container_id,
                            "backup_path": backup_path,
                        },
                    )

            # Re-raise original exception
            if isinstance(e, (NotFound, APIError, FileNotFoundError)):
                raise
            else:
                raise APIError(f"Container update failed: {str(e)}")

    async def delete_container(self, container_id: str) -> None:
        """
        Delete a container and clean up resources.

        Args:
            container_id: ID of the container to delete

        Raises:
            NotFound: If container doesn't exist
            APIError: If deletion fails
        """
        try:
            self.logger.log_debug("Deleting container", {"container_id": container_id})

            container = self.docker_client.containers.get(container_id)
            container_name = container.name

            # Stop container if running
            if container.status in ["running", "paused"]:
                container.stop()

            # Clean up health check resources
            self._cleanup_health_check_resources(container_id)

            # Remove container
            container.remove()

            # Clean up socket file
            socket_path = os.path.join(self.socket_dir, f"{container_name}.sock")
            if os.path.exists(socket_path):
                os.remove(socket_path)
                self.logger.log_debug(
                    "Cleaned up socket file", {"socket_path": socket_path}
                )

            self.logger.log_container_operation(
                "delete",
                container_id,
                {
                    "name": container_name,
                    "socket_path": socket_path,
                    "status": "deleted",
                },
            )

        except NotFound as e:
            self.logger.log_error(
                e, {"operation": "delete_container", "container_id": container_id}
            )
            raise
        except APIError as e:
            self.logger.log_error(
                e, {"operation": "delete_container", "container_id": container_id}
            )
            raise

    def _cleanup_health_check_resources(self, container_id: str) -> None:
        """
        Clean up health check resources for a container.

        Args:
            container_id: Container ID
        """
        # Stop health check task
        self._stop_health_check_task(container_id)

        # Remove health check configuration
        if container_id in self._health_check_configs:
            del self._health_check_configs[container_id]

        # Remove health status history
        if container_id in self._health_status_history:
            del self._health_status_history[container_id]

        self.logger.log_debug(
            "Health check resources cleaned up", {"container_id": container_id}
        )

    async def cleanup_all_health_checks(self) -> None:
        """
        Clean up all health check tasks and resources.
        """
        # Cancel all health check tasks
        for container_id in list(self._health_check_tasks.keys()):
            self._stop_health_check_task(container_id)

        # Clear all health check data
        self._health_check_configs.clear()
        self._health_status_history.clear()

        self.logger.log_debug("All health check resources cleaned up")

    async def get_container_status(self, container_id: str) -> ContainerStatus:
        """
        Get detailed status information for a container with resource usage monitoring.

        Args:
            container_id: ID of the container

        Returns:
            ContainerStatus: Detailed status information

        Raises:
            NotFound: If container doesn't exist
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.reload()  # Refresh container state

            # Parse container state
            state_str = container.attrs.get("State", {}).get("Status", "unknown")
            try:
                state = ContainerState(state_str)
            except ValueError:
                state = ContainerState.DEAD

            # Parse health status
            health_info = container.attrs.get("State", {}).get("Health", {})
            health_str = health_info.get("Status", "none")
            try:
                health = ContainerHealth(health_str)
            except ValueError:
                health = ContainerHealth.NONE

            # Calculate uptime
            uptime = None
            started_at = container.attrs.get("State", {}).get("StartedAt")
            if started_at and started_at != "0001-01-01T00:00:00Z":
                try:
                    # Handle ISO format with Z timezone indicator
                    if started_at.endswith("Z"):
                        started_at = started_at.replace("Z", "+00:00")
                    start_time = datetime.fromisoformat(started_at)
                    uptime = datetime.now(start_time.tzinfo) - start_time
                except (ValueError, AttributeError):
                    # Skip uptime calculation if parsing fails
                    pass

            # Check socket connection
            socket_path = os.path.join(self.socket_dir, f"{container.name}.sock")
            socket_connected = os.path.exists(socket_path)

            # Get resource usage metrics
            resource_usage = await self._get_resource_usage(container)

            return ContainerStatus(
                id=container_id,
                state=state,
                health=health,
                uptime=uptime,
                socket_connected=socket_connected,
                last_communication=None,  # Would be updated by socket handler
                resource_usage=resource_usage,
            )

        except NotFound as e:
            self.logger.log_error(
                e, {"operation": "get_container_status", "container_id": container_id}
            )
            raise

    async def list_containers(self) -> List[ContainerInfo]:
        """
        List all managed containers.

        Returns:
            List[ContainerInfo]: List of container information
        """
        try:
            containers = self.docker_client.containers.list(all=True)
            container_infos = []

            for container in containers:
                socket_path = os.path.join(self.socket_dir, f"{container.name}.sock")
                container_info = self._build_container_info(container, socket_path)
                container_infos.append(container_info)

            self.logger.log_debug("Listed containers", {"count": len(container_infos)})

            return container_infos

        except APIError as e:
            self.logger.log_error(e, {"operation": "list_containers"})
            raise

    def _build_container_info(self, container, socket_path: str) -> ContainerInfo:
        """
        Build ContainerInfo from Docker container object.

        Args:
            container: Docker container object
            socket_path: Path to Unix socket file

        Returns:
            ContainerInfo: Container information object
        """
        # Handle container.attrs safely for both real containers and mocks
        container_attrs = getattr(container, "attrs", {})

        # Parse creation time
        created_str = container_attrs.get("Created", "")
        try:
            # Handle ISO format with Z timezone indicator
            if created_str.endswith("Z"):
                created_str = created_str.replace("Z", "+00:00")
            created = datetime.fromisoformat(created_str)
        except (ValueError, AttributeError):
            # Default to current time if parsing fails
            created = datetime.now()

        # Parse environment variables
        env_list = container_attrs.get("Config", {}).get("Env", [])
        environment = {}
        for env_var in env_list:
            if isinstance(env_var, str) and "=" in env_var:
                key, value = env_var.split("=", 1)
                environment[key] = value

        # Parse port mappings
        ports = {}
        port_bindings = container_attrs.get("NetworkSettings", {}).get("Ports", {})
        for container_port, host_bindings in port_bindings.items():
            if host_bindings:
                port_num = container_port.split("/")[0]
                host_port = host_bindings[0].get("HostPort")
                if host_port:
                    try:
                        ports[port_num] = int(host_port)
                    except (ValueError, TypeError):
                        # Skip if port can't be converted to int
                        continue

        # Get image name safely
        image = getattr(container, "image", None)
        if image:
            image_tags = getattr(image, "tags", [])
            image_name = (
                image_tags[0] if image_tags else getattr(image, "id", "unknown")
            )
        else:
            image_name = "unknown"

        return ContainerInfo(
            id=container.id,
            name=container.name,
            status=container.status,
            image=image_name,
            created=created,
            socket_path=socket_path,
            ports=ports,
            environment=environment,
        )

    async def _get_resource_usage(self, container) -> Dict[str, Any]:
        """
        Get resource usage metrics for a container.

        Args:
            container: Docker container object

        Returns:
            Dict containing resource usage metrics
        """
        try:
            # Get container stats (non-blocking)
            stats = container.stats(stream=False)

            # Calculate CPU usage percentage
            cpu_usage = 0.0
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})

            if cpu_stats and precpu_stats:
                cpu_delta = cpu_stats.get("cpu_usage", {}).get(
                    "total_usage", 0
                ) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                    "system_cpu_usage", 0
                )

                if system_delta > 0:
                    cpu_count = cpu_stats.get("online_cpus", 1)
                    cpu_usage = (cpu_delta / system_delta) * cpu_count * 100.0

            # Calculate memory usage
            memory_stats = stats.get("memory_stats", {})
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)
            memory_percent = 0.0
            if memory_limit > 0:
                memory_percent = (memory_usage / memory_limit) * 100.0

            # Network I/O stats
            networks = stats.get("networks", {})
            network_rx = 0
            network_tx = 0
            for interface_stats in networks.values():
                network_rx += interface_stats.get("rx_bytes", 0)
                network_tx += interface_stats.get("tx_bytes", 0)

            # Block I/O stats
            blkio_stats = stats.get("blkio_stats", {})
            io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])
            disk_read = 0
            disk_write = 0
            for io_stat in io_service_bytes:
                if io_stat.get("op") == "Read":
                    disk_read += io_stat.get("value", 0)
                elif io_stat.get("op") == "Write":
                    disk_write += io_stat.get("value", 0)

            return {
                "cpu_percent": round(cpu_usage, 2),
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": round(memory_percent, 2),
                "network_rx_bytes": network_rx,
                "network_tx_bytes": network_tx,
                "disk_read_bytes": disk_read,
                "disk_write_bytes": disk_write,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.log_error(
                e, {"operation": "get_resource_usage", "container_id": container.id}
            )
            return {}

    def register_status_change_callback(self, callback: Callable) -> None:
        """
        Register a callback for container status changes.

        Args:
            callback: Function to call when container status changes
                     Signature: callback(container_id: str, old_state: ContainerState, new_state: ContainerState)
        """
        self._status_change_callbacks.append(callback)
        callback_name = getattr(callback, "__name__", str(callback))
        self.logger.log_debug(
            "Registered status change callback", {"callback": callback_name}
        )

    def register_health_check_callback(self, callback: Callable) -> None:
        """
        Register a callback for container health check failures.

        Args:
            callback: Function to call when health check fails
                     Signature: callback(container_id: str, health: ContainerHealth)
        """
        self._health_check_callbacks.append(callback)
        callback_name = getattr(callback, "__name__", str(callback))
        self.logger.log_debug(
            "Registered health check callback", {"callback": callback_name}
        )

    def register_crash_callback(self, callback: Callable) -> None:
        """
        Register a callback for container crashes.

        Args:
            callback: Function to call when container crashes
                     Signature: callback(container_id: str, exit_code: int, crash_details: dict)
        """
        self._crash_callbacks.append(callback)
        callback_name = getattr(callback, "__name__", str(callback))
        self.logger.log_debug("Registered crash callback", {"callback": callback_name})

    def register_resource_alert_callback(self, callback: Callable) -> None:
        """
        Register a callback for resource usage alerts.

        Args:
            callback: Function to call when resource thresholds are exceeded
                     Signature: callback(container_id: str, resource_type: str, current_value: float, threshold: float, usage_data: dict)
        """
        self._resource_alert_callbacks.append(callback)
        callback_name = getattr(callback, "__name__", str(callback))
        self.logger.log_debug(
            "Registered resource alert callback", {"callback": callback_name}
        )

    def set_resource_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Set resource usage thresholds for alerting.

        Args:
            thresholds: Dictionary of resource thresholds
                       Supported keys: cpu_percent, memory_percent,
                       disk_read_bytes_per_sec, disk_write_bytes_per_sec,
                       network_rx_bytes_per_sec, network_tx_bytes_per_sec
        """
        for key, value in thresholds.items():
            if key in self._resource_thresholds:
                self._resource_thresholds[key] = value
                self.logger.log_debug(
                    "Updated resource threshold", {"resource": key, "threshold": value}
                )

    def get_resource_thresholds(self) -> Dict[str, float]:
        """
        Get current resource usage thresholds.

        Returns:
            Dictionary of current resource thresholds
        """
        return self._resource_thresholds.copy()

    def enable_resource_monitoring(self) -> None:
        """Enable resource usage monitoring."""
        self._resource_monitoring_enabled = True
        self.logger.log_debug("Resource monitoring enabled", {})

    def disable_resource_monitoring(self) -> None:
        """Disable resource usage monitoring."""
        self._resource_monitoring_enabled = False
        self.logger.log_debug("Resource monitoring disabled", {})

    async def start_monitoring(self) -> None:
        """
        Start container status monitoring.

        This will continuously monitor all containers for status changes,
        health check failures, and crashes.
        """
        if self._monitoring_active:
            self.logger.log_debug("Container monitoring already active", {})
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.log_debug("Started container monitoring", {})

    async def stop_monitoring(self) -> None:
        """
        Stop container status monitoring.
        """
        if not self._monitoring_active:
            return

        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        self.logger.log_debug("Stopped container monitoring", {})

    async def _monitoring_loop(self) -> None:
        """
        Main monitoring loop that checks container status changes.
        """
        self.logger.log_debug("Starting container monitoring loop", {})

        while self._monitoring_active:
            try:
                # Get all containers
                containers = self.docker_client.containers.list(all=True)

                for container in containers:
                    await self._check_container_status(container)

                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                self.logger.log_error(e, {"operation": "monitoring_loop"})
                await asyncio.sleep(10)  # Wait longer on error

    async def _check_container_status(self, container) -> None:
        """
        Check a single container for status changes, health issues, and crashes.

        Args:
            container: Docker container object
        """
        try:
            container.reload()
            container_id = container.id

            # Parse current state
            state_str = container.attrs.get("State", {}).get("Status", "unknown")
            try:
                current_state = ContainerState(state_str)
            except ValueError:
                current_state = ContainerState.DEAD

            # Check for state changes
            previous_state = self._container_states.get(container_id)
            if previous_state and previous_state != current_state:
                self.logger.log_state_change(
                    container_id, previous_state.value, current_state.value
                )

                # Notify callbacks
                for callback in self._status_change_callbacks:
                    try:
                        await self._safe_callback(
                            callback, container_id, previous_state, current_state
                        )
                    except Exception as e:
                        callback_name = getattr(callback, "__name__", str(callback))
                        self.logger.log_error(
                            e,
                            {
                                "operation": "status_change_callback",
                                "container_id": container_id,
                                "callback": callback_name,
                            },
                        )

            # Update stored state
            self._container_states[container_id] = current_state

            # Check for crashes
            if current_state in [ContainerState.EXITED, ContainerState.DEAD]:
                await self._check_container_crash(container)

            # Check health status
            await self._check_container_health(container)

            # Check resource usage if monitoring is enabled and container is running
            if (
                self._resource_monitoring_enabled
                and current_state == ContainerState.RUNNING
            ):
                await self._check_resource_usage(container)

        except Exception as e:
            self.logger.log_error(
                e,
                {
                    "operation": "check_container_status",
                    "container_id": getattr(container, "id", "unknown"),
                },
            )

    async def _check_container_crash(self, container) -> None:
        """
        Check if a container has crashed and notify callbacks.

        Args:
            container: Docker container object
        """
        try:
            container_id = container.id
            state_info = container.attrs.get("State", {})
            exit_code = state_info.get("ExitCode", 0)

            # Consider non-zero exit codes as crashes
            if exit_code != 0:
                crash_details = {
                    "exit_code": exit_code,
                    "finished_at": state_info.get("FinishedAt"),
                    "error": state_info.get("Error", ""),
                    "oom_killed": state_info.get("OOMKilled", False),
                    "pid": state_info.get("Pid", 0),
                }

                self.logger.log_error(
                    Exception(f"Container crashed with exit code {exit_code}"),
                    {
                        "operation": "container_crash_detected",
                        "container_id": container_id,
                        "crash_details": crash_details,
                    },
                )

                # Notify crash callbacks
                for callback in self._crash_callbacks:
                    try:
                        await self._safe_callback(
                            callback, container_id, exit_code, crash_details
                        )
                    except Exception as e:
                        callback_name = getattr(callback, "__name__", str(callback))
                        self.logger.log_error(
                            e,
                            {
                                "operation": "crash_callback",
                                "container_id": container_id,
                                "callback": callback_name,
                            },
                        )

        except Exception as e:
            self.logger.log_error(
                e,
                {
                    "operation": "check_container_crash",
                    "container_id": getattr(container, "id", "unknown"),
                },
            )

    async def _check_container_health(self, container) -> None:
        """
        Check container health status and notify callbacks on failures.

        Args:
            container: Docker container object
        """
        try:
            container_id = container.id
            health_info = container.attrs.get("State", {}).get("Health", {})
            health_str = health_info.get("Status", "none")

            try:
                health = ContainerHealth(health_str)
            except ValueError:
                health = ContainerHealth.NONE

            # Check for health failures
            if health == ContainerHealth.UNHEALTHY:
                health_details = {
                    "status": health_str,
                    "failing_streak": health_info.get("FailingStreak", 0),
                    "log": health_info.get("Log", []),
                }

                self.logger.log_debug(
                    "Container health check failed",
                    {"container_id": container_id, "health_details": health_details},
                )

                # Notify health check callbacks
                for callback in self._health_check_callbacks:
                    try:
                        await self._safe_callback(callback, container_id, health)
                    except Exception as e:
                        callback_name = getattr(callback, "__name__", str(callback))
                        self.logger.log_error(
                            e,
                            {
                                "operation": "health_check_callback",
                                "container_id": container_id,
                                "callback": callback_name,
                            },
                        )

        except Exception as e:
            self.logger.log_error(
                e,
                {
                    "operation": "check_container_health",
                    "container_id": getattr(container, "id", "unknown"),
                },
            )

    # Enhanced Health Check System

    def set_health_check_config(
        self, container_id: str, config: HealthCheckConfig
    ) -> None:
        """
        Set health check configuration for a container.

        Args:
            container_id: Container ID
            config: Health check configuration
        """
        self._health_check_configs[container_id] = config

        # Initialize health status history if not exists
        if container_id not in self._health_status_history:
            self._health_status_history[container_id] = HealthStatusHistory(
                container_id=container_id
            )

        # Start health check task if enabled
        if config.enabled:
            self._start_health_check_task(container_id)
        else:
            self._stop_health_check_task(container_id)

        self.logger.log_debug(
            "Health check configuration set",
            {"container_id": container_id, "config": config.dict()},
        )

    def get_health_check_config(self, container_id: str) -> Optional[HealthCheckConfig]:
        """
        Get health check configuration for a container.

        Args:
            container_id: Container ID

        Returns:
            Health check configuration or None if not set
        """
        return self._health_check_configs.get(container_id)

    def get_health_status_history(
        self, container_id: str
    ) -> Optional[HealthStatusHistory]:
        """
        Get health status history for a container.

        Args:
            container_id: Container ID

        Returns:
            Health status history or None if not available
        """
        return self._health_status_history.get(container_id)

    def get_default_health_config(self) -> HealthCheckConfig:
        """
        Get default health check configuration.

        Returns:
            Default health check configuration
        """
        if self._default_health_config is None:
            self._default_health_config = HealthCheckConfig()
        return self._default_health_config

    def set_default_health_config(self, config: HealthCheckConfig) -> None:
        """
        Set default health check configuration for new containers.

        Args:
            config: Default health check configuration
        """
        self._default_health_config = config
        self.logger.log_debug(
            "Default health check configuration set", {"config": config.dict()}
        )

    def _start_health_check_task(self, container_id: str) -> None:
        """
        Start health check task for a container.

        Args:
            container_id: Container ID
        """
        # Stop existing task if running
        self._stop_health_check_task(container_id)

        # Start new task
        task = asyncio.create_task(self._health_check_loop(container_id))
        self._health_check_tasks[container_id] = task

        self.logger.log_debug(
            "Health check task started", {"container_id": container_id}
        )

    def _stop_health_check_task(self, container_id: str) -> None:
        """
        Stop health check task for a container.

        Args:
            container_id: Container ID
        """
        if container_id in self._health_check_tasks:
            task = self._health_check_tasks[container_id]
            if not task.done():
                task.cancel()
            del self._health_check_tasks[container_id]

            self.logger.log_debug(
                "Health check task stopped", {"container_id": container_id}
            )

    async def _health_check_loop(self, container_id: str) -> None:
        """
        Health check loop for a specific container.

        Args:
            container_id: Container ID
        """
        config = self._health_check_configs.get(container_id)
        if not config or not config.enabled:
            return

        # Wait for start period
        await asyncio.sleep(config.start_period)

        while True:
            try:
                # Check if container still exists
                try:
                    container = self.docker_client.containers.get(container_id)
                except NotFound:
                    self.logger.log_debug(
                        "Container not found, stopping health checks",
                        {"container_id": container_id},
                    )
                    break

                # Perform health check
                result = await self._perform_health_check(container, config)

                # Update history
                history = self._health_status_history.get(container_id)
                if history:
                    history.add_result(result)

                    # Check if recovery is needed
                    if history.should_recover(config):
                        await self._attempt_recovery(container_id, config, history)

                # Notify callbacks if unhealthy
                if result.health == ContainerHealth.UNHEALTHY:
                    for callback in self._health_check_callbacks:
                        try:
                            await self._safe_callback(
                                callback, container_id, result.health
                            )
                        except Exception as e:
                            callback_name = getattr(callback, "__name__", str(callback))
                            self.logger.log_error(
                                e,
                                {
                                    "operation": "enhanced_health_check_callback",
                                    "container_id": container_id,
                                    "callback": callback_name,
                                },
                            )

                # Wait for next check
                await asyncio.sleep(config.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.log_error(
                    e,
                    {
                        "operation": "health_check_loop",
                        "container_id": container_id,
                    },
                )
                # Continue after error with shorter interval
                await asyncio.sleep(min(config.interval, 30))

    async def _perform_health_check(
        self, container, config: HealthCheckConfig
    ) -> HealthCheckResult:
        """
        Perform a health check on a container.

        Args:
            container: Docker container object
            config: Health check configuration

        Returns:
            Health check result
        """
        start_time = datetime.now()
        container_id = container.id

        try:
            success = False
            error_message = None
            details = {}

            if config.check_type == HealthCheckType.HTTP:
                success, error_message, details = await self._http_health_check(
                    container, config
                )
            elif config.check_type == HealthCheckType.TCP:
                success, error_message, details = await self._tcp_health_check(
                    container, config
                )
            elif config.check_type == HealthCheckType.COMMAND:
                success, error_message, details = await self._command_health_check(
                    container, config
                )
            elif config.check_type == HealthCheckType.SOCKET:
                success, error_message, details = await self._socket_health_check(
                    container, config
                )
            else:
                # Default to Docker's built-in health check
                success, error_message, details = await self._docker_health_check(
                    container, config
                )

            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()

            # Determine health status
            health = ContainerHealth.HEALTHY if success else ContainerHealth.UNHEALTHY

            return HealthCheckResult(
                container_id=container_id,
                timestamp=start_time,
                health=health,
                check_type=config.check_type,
                success=success,
                response_time=response_time,
                error_message=error_message,
                details=details,
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return HealthCheckResult(
                container_id=container_id,
                timestamp=start_time,
                health=ContainerHealth.UNHEALTHY,
                check_type=config.check_type,
                success=False,
                response_time=response_time,
                error_message=str(e),
                details={"exception": type(e).__name__},
            )

    async def _http_health_check(
        self, container, config: HealthCheckConfig
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Perform HTTP health check.

        Args:
            container: Docker container object
            config: Health check configuration

        Returns:
            Tuple of (success, error_message, details)
        """
        import aiohttp

        try:
            # Get container IP and port
            network_settings = container.attrs.get("NetworkSettings", {})
            ip_address = network_settings.get("IPAddress", "localhost")
            port = config.port or 80
            endpoint = config.endpoint or "/health"

            url = f"http://{ip_address}:{port}{endpoint}"

            timeout = aiohttp.ClientTimeout(total=config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    success = 200 <= response.status < 400
                    details = {
                        "url": url,
                        "status_code": response.status,
                        "response_headers": dict(response.headers),
                    }

                    if success:
                        return True, None, details
                    else:
                        return False, f"HTTP {response.status}", details

        except asyncio.TimeoutError:
            return False, "HTTP timeout", {"url": url}
        except Exception as e:
            return (
                False,
                f"HTTP error: {str(e)}",
                {"url": url, "exception": type(e).__name__},
            )

    async def _tcp_health_check(
        self, container, config: HealthCheckConfig
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Perform TCP health check.

        Args:
            container: Docker container object
            config: Health check configuration

        Returns:
            Tuple of (success, error_message, details)
        """
        try:
            # Get container IP and port
            network_settings = container.attrs.get("NetworkSettings", {})
            ip_address = network_settings.get("IPAddress", "localhost")
            port = config.port or 80

            # Try to connect
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip_address, port), timeout=config.timeout
            )

            writer.close()
            await writer.wait_closed()

            return True, None, {"host": ip_address, "port": port}

        except asyncio.TimeoutError:
            return False, "TCP timeout", {"host": ip_address, "port": port}
        except Exception as e:
            return (
                False,
                f"TCP error: {str(e)}",
                {"host": ip_address, "port": port, "exception": type(e).__name__},
            )

    async def _command_health_check(
        self, container, config: HealthCheckConfig
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Perform command-based health check.

        Args:
            container: Docker container object
            config: Health check configuration

        Returns:
            Tuple of (success, error_message, details)
        """
        try:
            if not config.command:
                return False, "No command specified", {}

            # Execute command in container
            result = container.exec_run(config.command, stdout=True, stderr=True)

            success = result.exit_code == 0
            details = {
                "command": config.command,
                "exit_code": result.exit_code,
                "output": result.output.decode("utf-8") if result.output else "",
            }

            if success:
                return True, None, details
            else:
                return (
                    False,
                    f"Command failed with exit code {result.exit_code}",
                    details,
                )

        except Exception as e:
            return (
                False,
                f"Command error: {str(e)}",
                {"command": config.command, "exception": type(e).__name__},
            )

    async def _socket_health_check(
        self, container, config: HealthCheckConfig
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Perform Unix socket health check.

        Args:
            container: Docker container object
            config: Health check configuration

        Returns:
            Tuple of (success, error_message, details)
        """
        try:
            socket_path = os.path.join(self.socket_dir, f"{container.name}.sock")

            if not os.path.exists(socket_path):
                return False, "Socket file not found", {"socket_path": socket_path}

            # Try to connect to socket
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path), timeout=config.timeout
            )

            # Send ping message
            ping_message = '{"command": "ping", "data": {}}\n'
            writer.write(ping_message.encode())
            await writer.drain()

            # Read response
            response = await asyncio.wait_for(reader.readline(), timeout=config.timeout)

            writer.close()
            await writer.wait_closed()

            # Check if we got a valid response
            if response:
                return (
                    True,
                    None,
                    {"socket_path": socket_path, "response": response.decode().strip()},
                )
            else:
                return False, "No response from socket", {"socket_path": socket_path}

        except asyncio.TimeoutError:
            return False, "Socket timeout", {"socket_path": socket_path}
        except Exception as e:
            return (
                False,
                f"Socket error: {str(e)}",
                {"socket_path": socket_path, "exception": type(e).__name__},
            )

    async def _docker_health_check(
        self, container, config: HealthCheckConfig
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Use Docker's built-in health check.

        Args:
            container: Docker container object
            config: Health check configuration

        Returns:
            Tuple of (success, error_message, details)
        """
        try:
            container.reload()
            health_info = container.attrs.get("State", {}).get("Health", {})
            health_str = health_info.get("Status", "none")

            success = health_str == "healthy"
            details = {
                "status": health_str,
                "failing_streak": health_info.get("FailingStreak", 0),
                "log": health_info.get("Log", []),
            }

            if success:
                return True, None, details
            else:
                return False, f"Docker health check: {health_str}", details

        except Exception as e:
            return (
                False,
                f"Docker health check error: {str(e)}",
                {"exception": type(e).__name__},
            )

    async def _attempt_recovery(
        self, container_id: str, config: HealthCheckConfig, history: HealthStatusHistory
    ) -> None:
        """
        Attempt to recover an unhealthy container.

        Args:
            container_id: Container ID
            config: Health check configuration
            history: Health status history
        """
        try:
            history.record_recovery_attempt()

            self.logger.log_debug(
                "Attempting container recovery",
                {
                    "container_id": container_id,
                    "recovery_action": config.recovery_action,
                    "attempt": history.recovery_attempts,
                },
            )

            if config.recovery_action == "restart":
                await self.restart_container(container_id)
            elif config.recovery_action == "recreate":
                # Get container info before deletion
                container = self.docker_client.containers.get(container_id)
                container_config = container.attrs.get("Config", {})
                host_config = container.attrs.get("HostConfig", {})

                # Stop and remove container
                await self.delete_container(container_id)

                # Recreate container with same configuration
                # This is a simplified recreation - in practice, you'd want to
                # preserve all the original configuration
                new_config = ContainerConfig(
                    image=container.image.id,
                    name=container.name,
                    environment={},  # Would need to parse from container_config
                    volumes={},  # Would need to parse from host_config
                    ports={},  # Would need to parse from host_config
                )

                new_container = await self.create_container(new_config)
                await self.start_container(new_container.id)

                # Update container_id references
                if container_id in self._health_check_configs:
                    self._health_check_configs[new_container.id] = (
                        self._health_check_configs.pop(container_id)
                    )
                if container_id in self._health_status_history:
                    old_history = self._health_status_history.pop(container_id)
                    old_history.container_id = new_container.id
                    self._health_status_history[new_container.id] = old_history

            self.logger.log_container_operation(
                "recovery",
                container_id,
                {
                    "recovery_action": config.recovery_action,
                    "attempt": history.recovery_attempts,
                    "status": "completed",
                },
            )

        except Exception as e:
            self.logger.log_error(
                e,
                {
                    "operation": "container_recovery",
                    "container_id": container_id,
                    "recovery_action": config.recovery_action,
                    "attempt": history.recovery_attempts,
                },
            )

    async def _check_resource_usage(self, container) -> None:
        """
        Check container resource usage and trigger alerts if thresholds are exceeded.

        Args:
            container: Docker container object
        """
        try:
            container_id = container.id

            # Get current resource usage
            resource_usage = await self._get_resource_usage(container)
            if not resource_usage:
                return

            # Store resource usage history (keep last 10 entries)
            if container_id not in self._resource_usage_history:
                self._resource_usage_history[container_id] = []

            history = self._resource_usage_history[container_id]
            history.append(resource_usage)
            if len(history) > 10:
                history.pop(0)

            # Calculate rates for disk and network I/O if we have previous data
            if len(history) >= 2:
                prev_usage = history[-2]
                current_usage = history[-1]

                # Calculate time delta
                prev_time = datetime.fromisoformat(prev_usage["timestamp"])
                current_time = datetime.fromisoformat(current_usage["timestamp"])
                time_delta = (current_time - prev_time).total_seconds()

                if time_delta > 0:
                    # Calculate disk I/O rates
                    disk_read_rate = (
                        current_usage["disk_read_bytes"] - prev_usage["disk_read_bytes"]
                    ) / time_delta
                    disk_write_rate = (
                        current_usage["disk_write_bytes"]
                        - prev_usage["disk_write_bytes"]
                    ) / time_delta

                    # Calculate network I/O rates
                    network_rx_rate = (
                        current_usage["network_rx_bytes"]
                        - prev_usage["network_rx_bytes"]
                    ) / time_delta
                    network_tx_rate = (
                        current_usage["network_tx_bytes"]
                        - prev_usage["network_tx_bytes"]
                    ) / time_delta

                    # Add rates to current usage data
                    resource_usage["disk_read_bytes_per_sec"] = disk_read_rate
                    resource_usage["disk_write_bytes_per_sec"] = disk_write_rate
                    resource_usage["network_rx_bytes_per_sec"] = network_rx_rate
                    resource_usage["network_tx_bytes_per_sec"] = network_tx_rate

            # Check thresholds and trigger alerts
            await self._check_resource_thresholds(container_id, resource_usage)

        except Exception as e:
            self.logger.log_error(
                e,
                {
                    "operation": "check_resource_usage",
                    "container_id": getattr(container, "id", "unknown"),
                },
            )

    async def _check_resource_thresholds(
        self, container_id: str, resource_usage: Dict[str, Any]
    ) -> None:
        """
        Check if resource usage exceeds thresholds and trigger alerts.

        Args:
            container_id: Container ID
            resource_usage: Current resource usage data
        """
        try:
            alerts_triggered = []

            # Check CPU threshold
            cpu_percent = resource_usage.get("cpu_percent", 0)
            if cpu_percent > self._resource_thresholds["cpu_percent"]:
                alerts_triggered.append(
                    {
                        "resource_type": "cpu_percent",
                        "current_value": cpu_percent,
                        "threshold": self._resource_thresholds["cpu_percent"],
                    }
                )

            # Check memory threshold
            memory_percent = resource_usage.get("memory_percent", 0)
            if memory_percent > self._resource_thresholds["memory_percent"]:
                alerts_triggered.append(
                    {
                        "resource_type": "memory_percent",
                        "current_value": memory_percent,
                        "threshold": self._resource_thresholds["memory_percent"],
                    }
                )

            # Check disk I/O thresholds (if rates are available)
            disk_read_rate = resource_usage.get("disk_read_bytes_per_sec", 0)
            if disk_read_rate > self._resource_thresholds["disk_read_bytes_per_sec"]:
                alerts_triggered.append(
                    {
                        "resource_type": "disk_read_bytes_per_sec",
                        "current_value": disk_read_rate,
                        "threshold": self._resource_thresholds[
                            "disk_read_bytes_per_sec"
                        ],
                    }
                )

            disk_write_rate = resource_usage.get("disk_write_bytes_per_sec", 0)
            if disk_write_rate > self._resource_thresholds["disk_write_bytes_per_sec"]:
                alerts_triggered.append(
                    {
                        "resource_type": "disk_write_bytes_per_sec",
                        "current_value": disk_write_rate,
                        "threshold": self._resource_thresholds[
                            "disk_write_bytes_per_sec"
                        ],
                    }
                )

            # Check network I/O thresholds (if rates are available)
            network_rx_rate = resource_usage.get("network_rx_bytes_per_sec", 0)
            if network_rx_rate > self._resource_thresholds["network_rx_bytes_per_sec"]:
                alerts_triggered.append(
                    {
                        "resource_type": "network_rx_bytes_per_sec",
                        "current_value": network_rx_rate,
                        "threshold": self._resource_thresholds[
                            "network_rx_bytes_per_sec"
                        ],
                    }
                )

            network_tx_rate = resource_usage.get("network_tx_bytes_per_sec", 0)
            if network_tx_rate > self._resource_thresholds["network_tx_bytes_per_sec"]:
                alerts_triggered.append(
                    {
                        "resource_type": "network_tx_bytes_per_sec",
                        "current_value": network_tx_rate,
                        "threshold": self._resource_thresholds[
                            "network_tx_bytes_per_sec"
                        ],
                    }
                )

            # Trigger alerts for each threshold exceeded
            for alert in alerts_triggered:
                self.logger.log_debug(
                    "Resource threshold exceeded",
                    {
                        "container_id": container_id,
                        "resource_type": alert["resource_type"],
                        "current_value": alert["current_value"],
                        "threshold": alert["threshold"],
                    },
                )

                # Notify resource alert callbacks
                for callback in self._resource_alert_callbacks:
                    try:
                        await self._safe_callback(
                            callback,
                            container_id,
                            alert["resource_type"],
                            alert["current_value"],
                            alert["threshold"],
                            resource_usage,
                        )
                    except Exception as e:
                        callback_name = getattr(callback, "__name__", str(callback))
                        self.logger.log_error(
                            e,
                            {
                                "operation": "resource_alert_callback",
                                "container_id": container_id,
                                "callback": callback_name,
                            },
                        )

        except Exception as e:
            self.logger.log_error(
                e,
                {
                    "operation": "check_resource_thresholds",
                    "container_id": container_id,
                },
            )

    def get_resource_usage_history(
        self, container_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get resource usage history for a container.

        Args:
            container_id: Container ID
            limit: Maximum number of history entries to return

        Returns:
            List of resource usage data points
        """
        history = self._resource_usage_history.get(container_id, [])
        return history[-limit:] if limit > 0 else history

    async def _safe_callback(self, callback: Callable, *args) -> None:
        """
        Safely execute a callback, handling both sync and async functions.

        Args:
            callback: The callback function to execute
            *args: Arguments to pass to the callback
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            callback_name = getattr(callback, "__name__", str(callback))
            self.logger.log_error(
                e,
                {
                    "operation": "safe_callback",
                    "callback": callback_name,
                    "args": str(args),
                },
            )
