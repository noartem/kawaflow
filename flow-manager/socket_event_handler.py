"""
Socket.IO Event Handler for Container Lifecycle Management

This module provides the SocketIOEventHandler class that handles all Socket.IO events
for container operations, message communication, and status monitoring.
"""

import asyncio
from typing import Dict, Any, Optional
import socketio
from docker.errors import APIError, ImageNotFound, NotFound

from container_manager import ContainerManager
from socket_communication_handler import (
    SocketCommunicationHandler,
    SocketCommunicationError,
    SocketTimeoutError,
    SocketConnectionError,
)
from system_logger import SystemLogger
from user_activity_logger import UserActivityLogger
from models import (
    ContainerConfig,
    CreateContainerEvent,
    ContainerOperationEvent,
    UpdateContainerEvent,
    SendMessageEvent,
    ErrorResponse,
    HealthCheckConfig,
    HealthCheckConfigEvent,
)


class SocketIOEventHandler:
    """
    Handles Socket.IO events for container lifecycle management.

    This class processes incoming Socket.IO events, validates event data,
    coordinates with ContainerManager and SocketCommunicationHandler,
    and emits responses and status updates to clients.
    """

    def __init__(
        self,
        sio: socketio.AsyncServer,
        container_manager: ContainerManager,
        socket_handler: SocketCommunicationHandler,
        system_logger: Optional[SystemLogger] = None,
        user_logger: Optional[UserActivityLogger] = None,
    ):
        """
        Initialize the Socket.IO event handler.

        Args:
            sio: Socket.IO server instance
            container_manager: Container management instance
            socket_handler: Socket communication handler instance
            system_logger: System logger instance (optional)
            user_logger: User activity logger instance (optional)
        """
        self.sio = sio
        self.container_manager = container_manager
        self.socket_handler = socket_handler
        self.system_logger = system_logger or SystemLogger()
        self.user_logger = user_logger or UserActivityLogger(sio)

        # Register event handlers
        self._register_event_handlers()

        # Register container manager callbacks for status monitoring
        self._register_container_callbacks()

        self.system_logger.log_debug(
            "SocketIOEventHandler initialized", {"handlers_registered": True}
        )

    def _register_event_handlers(self) -> None:
        """Register all Socket.IO event handlers."""
        # Container lifecycle events
        self.sio.on("create_container", self.handle_create_container)
        self.sio.on("start_container", self.handle_start_container)
        self.sio.on("stop_container", self.handle_stop_container)
        self.sio.on("restart_container", self.handle_restart_container)
        self.sio.on("update_container", self.handle_update_container)
        self.sio.on("delete_container", self.handle_delete_container)

        # Communication events
        self.sio.on("send_message", self.handle_send_message)

        # Status and monitoring events
        self.sio.on("get_container_status", self.handle_get_status)
        self.sio.on("list_containers", self.handle_list_containers)

        # Resource monitoring events
        self.sio.on("get_resource_thresholds", self.handle_get_resource_thresholds)
        self.sio.on("set_resource_thresholds", self.handle_set_resource_thresholds)
        self.sio.on(
            "get_resource_usage_history", self.handle_get_resource_usage_history
        )
        self.sio.on(
            "enable_resource_monitoring", self.handle_enable_resource_monitoring
        )
        self.sio.on(
            "disable_resource_monitoring", self.handle_disable_resource_monitoring
        )

        # Enhanced health check events
        self.sio.on("set_health_check_config", self.handle_set_health_check_config)
        self.sio.on("get_health_check_config", self.handle_get_health_check_config)
        self.sio.on("get_health_status_history", self.handle_get_health_status_history)
        self.sio.on("set_default_health_config", self.handle_set_default_health_config)
        self.sio.on("get_default_health_config", self.handle_get_default_health_config)

        # Connection events
        self.sio.on("connect", self.handle_connect)
        self.sio.on("disconnect", self.handle_disconnect)

    def _register_container_callbacks(self) -> None:
        """Register callbacks for container status monitoring."""
        self.container_manager.register_status_change_callback(self._on_status_change)
        self.container_manager.register_health_check_callback(
            self._on_health_check_failure
        )
        self.container_manager.register_crash_callback(self._on_container_crash)
        self.container_manager.register_resource_alert_callback(self._on_resource_alert)

    async def handle_connect(self, sid: str, environ: Dict[str, Any]) -> None:
        """
        Handle client connection.

        Args:
            sid: Socket session ID
            environ: Connection environment
        """
        self.system_logger.log_socket_event(
            "connect", sid, {"environ_keys": list(environ.keys())}
        )
        await self.sio.emit(
            "connected", {"message": "Connected to flow-manager"}, to=sid
        )

    async def handle_disconnect(self, sid: str) -> None:
        """
        Handle client disconnection.

        Args:
            sid: Socket session ID
        """
        self.system_logger.log_socket_event("disconnect", sid, {})

    async def handle_create_container(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle create_container Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container configuration
        """
        try:
            self.system_logger.log_socket_event("create_container", sid, data)

            # Validate event data
            event_data = CreateContainerEvent(**data)

            # Create container configuration
            config = ContainerConfig(
                image=event_data.image,
                name=event_data.name,
                environment=event_data.environment,
                volumes=event_data.volumes,
                ports=event_data.ports,
            )

            # Create container
            container_info = await self.container_manager.create_container(config)

            # Setup socket for communication
            await self.socket_handler.setup_socket(container_info.id)

            # Log user activity
            await self.user_logger.log_container_created(
                container_info.id, container_info.name, container_info.image
            )

            # Emit success response
            await self.sio.emit(
                "container_created",
                {
                    "container_id": container_info.id,
                    "name": container_info.name,
                    "image": container_info.image,
                    "status": container_info.status,
                    "socket_path": container_info.socket_path,
                    "ports": container_info.ports,
                },
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "create_container", e, data)

    async def handle_start_container(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle start_container Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container ID
        """
        try:
            self.system_logger.log_socket_event("start_container", sid, data)

            # Validate event data
            event_data = ContainerOperationEvent(**data)

            # Start container
            await self.container_manager.start_container(event_data.container_id)

            # Get container info for logging
            containers = await self.container_manager.list_containers()
            container = next(
                (c for c in containers if c.id == event_data.container_id), None
            )
            container_name = container.name if container else event_data.container_id

            # Log user activity
            await self.user_logger.log_container_started(
                event_data.container_id, container_name
            )

            # Emit success response
            await self.sio.emit(
                "container_started",
                {"container_id": event_data.container_id, "status": "running"},
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "start_container", e, data)

    async def handle_stop_container(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle stop_container Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container ID
        """
        try:
            self.system_logger.log_socket_event("stop_container", sid, data)

            # Validate event data
            event_data = ContainerOperationEvent(**data)

            # Get container info for logging
            containers = await self.container_manager.list_containers()
            container = next(
                (c for c in containers if c.id == event_data.container_id), None
            )
            container_name = container.name if container else event_data.container_id

            # Stop container
            await self.container_manager.stop_container(event_data.container_id)

            # Log user activity
            await self.user_logger.log_container_stopped(
                event_data.container_id, container_name
            )

            # Emit success response
            await self.sio.emit(
                "container_stopped",
                {"container_id": event_data.container_id, "status": "stopped"},
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "stop_container", e, data)

    async def handle_restart_container(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle restart_container Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container ID
        """
        try:
            self.system_logger.log_socket_event("restart_container", sid, data)

            # Validate event data
            event_data = ContainerOperationEvent(**data)

            # Get container info for logging
            containers = await self.container_manager.list_containers()
            container = next(
                (c for c in containers if c.id == event_data.container_id), None
            )
            container_name = container.name if container else event_data.container_id

            # Restart container
            await self.container_manager.restart_container(event_data.container_id)

            # Log user activity
            await self.user_logger.log_container_restarted(
                event_data.container_id, container_name
            )

            # Emit success response
            await self.sio.emit(
                "container_restarted",
                {"container_id": event_data.container_id, "status": "running"},
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "restart_container", e, data)

    async def handle_update_container(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle update_container Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container ID and code path
        """
        try:
            self.system_logger.log_socket_event("update_container", sid, data)

            # Validate event data
            event_data = UpdateContainerEvent(**data)

            # Get container info for logging
            containers = await self.container_manager.list_containers()
            container = next(
                (c for c in containers if c.id == event_data.container_id), None
            )
            container_name = container.name if container else event_data.container_id

            # Update container
            await self.container_manager.update_container(
                event_data.container_id, event_data.code_path
            )

            # Log user activity
            await self.user_logger.log_container_updated(
                event_data.container_id, container_name
            )

            # Emit success response
            await self.sio.emit(
                "container_updated",
                {
                    "container_id": event_data.container_id,
                    "code_path": event_data.code_path,
                    "status": "updated",
                },
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "update_container", e, data)

    async def handle_delete_container(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle delete_container Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container ID
        """
        try:
            self.system_logger.log_socket_event("delete_container", sid, data)

            # Validate event data
            event_data = ContainerOperationEvent(**data)

            # Get container info for logging
            containers = await self.container_manager.list_containers()
            container = next(
                (c for c in containers if c.id == event_data.container_id), None
            )
            container_name = container.name if container else event_data.container_id

            # Clean up socket first
            await self.socket_handler.cleanup_socket(event_data.container_id)

            # Delete container
            await self.container_manager.delete_container(event_data.container_id)

            # Log user activity
            await self.user_logger.log_container_deleted(
                event_data.container_id, container_name
            )

            # Emit success response
            await self.sio.emit(
                "container_deleted",
                {"container_id": event_data.container_id, "status": "deleted"},
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "delete_container", e, data)

    async def handle_send_message(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle send_message Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container ID and message
        """
        try:
            self.system_logger.log_socket_event("send_message", sid, data)

            # Validate event data
            event_data = SendMessageEvent(**data)

            # Send message to container
            await self.socket_handler.send_message(
                event_data.container_id, event_data.message
            )

            # Log user activity
            await self.user_logger.log_container_message(
                event_data.container_id, event_data.message, "sent"
            )

            # Emit success response
            await self.sio.emit(
                "message_sent",
                {
                    "container_id": event_data.container_id,
                    "message": event_data.message,
                    "status": "sent",
                },
                to=sid,
            )

        except SocketTimeoutError as e:
            await self._emit_error(sid, "send_message", e, data, "socket_timeout_error")
        except SocketConnectionError as e:
            await self._emit_error(
                sid, "send_message", e, data, "socket_connection_error"
            )
        except SocketCommunicationError as e:
            await self._emit_error(
                sid, "send_message", e, data, "socket_communication_error"
            )
        except Exception as e:
            await self._emit_error(sid, "send_message", e, data)

    async def handle_get_status(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle get_container_status Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data containing container ID
        """
        try:
            self.system_logger.log_socket_event("get_container_status", sid, data)

            # Validate event data
            event_data = ContainerOperationEvent(**data)

            # Get container status
            status = await self.container_manager.get_container_status(
                event_data.container_id
            )

            # Emit status response
            await self.sio.emit(
                "container_status",
                {
                    "container_id": event_data.container_id,
                    "state": status.state.value,
                    "health": status.health.value,
                    "uptime": str(status.uptime) if status.uptime else None,
                    "socket_connected": status.socket_connected,
                    "last_communication": (
                        status.last_communication.isoformat()
                        if status.last_communication
                        else None
                    ),
                    "resource_usage": status.resource_usage,
                },
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "get_container_status", e, data)

    async def handle_list_containers(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Handle list_containers Socket.IO event.

        Args:
            sid: Socket session ID
            data: Event data (unused for list operation)
        """
        try:
            self.system_logger.log_socket_event("list_containers", sid, data)

            # List all containers
            containers = await self.container_manager.list_containers()

            # Format container list
            container_list = []
            for container in containers:
                container_list.append(
                    {
                        "id": container.id,
                        "name": container.name,
                        "status": container.status,
                        "image": container.image,
                        "created": container.created.isoformat(),
                        "socket_path": container.socket_path,
                        "ports": container.ports,
                    }
                )

            # Emit container list
            await self.sio.emit(
                "container_list",
                {"containers": container_list, "count": len(container_list)},
                to=sid,
            )

        except Exception as e:
            await self._emit_error(sid, "list_containers", e, data)

    async def _emit_error(
        self,
        sid: str,
        operation: str,
        error: Exception,
        data: Dict[str, Any],
        error_type: Optional[str] = None,
    ) -> None:
        """
        Emit standardized error response.

        Args:
            sid: Socket session ID
            operation: Operation that failed
            error: Exception that occurred
            data: Original event data
            error_type: Specific error type (optional)
        """
        # Determine error type
        if error_type is None:
            if isinstance(error, ImageNotFound):
                error_type = "image_not_found"
            elif isinstance(error, NotFound):
                error_type = "container_not_found"
            elif isinstance(error, APIError):
                error_type = "docker_api_error"
            elif isinstance(
                error,
                (SocketCommunicationError, SocketTimeoutError, SocketConnectionError),
            ):
                error_type = "socket_error"
            else:
                error_type = "system_error"

        # Log error
        self.system_logger.log_error(
            error, {"operation": operation, "sid": sid, "data": data}
        )

        # Create error response
        error_response = ErrorResponse(
            error_type=error_type,
            message=str(error),
            details={"operation": operation, "data": data},
        )

        # Emit error to client
        await self.sio.emit("error", error_response.dict(), to=sid)

        # Log user activity for error
        container_id = data.get("container_id", "unknown")
        await self.user_logger.log_container_error(container_id, str(error), operation)

    # Container callback methods for status monitoring

    async def _on_status_change(
        self, container_id: str, old_state: str, new_state: str
    ) -> None:
        """
        Callback for container status changes.

        Args:
            container_id: Container ID
            old_state: Previous state
            new_state: New state
        """
        try:
            # Emit status change to all clients
            await self.sio.emit(
                "status_changed",
                {
                    "container_id": container_id,
                    "old_state": old_state,
                    "new_state": new_state,
                    "timestamp": asyncio.get_event_loop().time(),
                },
            )

            # Log user activity
            await self.user_logger.log_user_activity(
                "status_change",
                container_id,
                f"Container status changed from {old_state} to {new_state}",
                {"old_state": old_state, "new_state": new_state},
            )

        except Exception as e:
            self.system_logger.log_error(
                e, {"callback": "_on_status_change", "container_id": container_id}
            )

    async def _on_health_check_failure(self, container_id: str, health: str) -> None:
        """
        Callback for container health check failures.

        Args:
            container_id: Container ID
            health: Health status
        """
        try:
            # Emit health warning to all clients
            await self.sio.emit(
                "container_health_warning",
                {
                    "container_id": container_id,
                    "health": health,
                    "timestamp": asyncio.get_event_loop().time(),
                },
            )

            # Log user activity
            await self.user_logger.log_user_activity(
                "health_warning",
                container_id,
                f"Container health check failed: {health}",
                {"health": health},
            )

        except Exception as e:
            self.system_logger.log_error(
                e,
                {"callback": "_on_health_check_failure", "container_id": container_id},
            )

    async def _on_container_crash(
        self, container_id: str, exit_code: int, crash_details: Dict[str, Any]
    ) -> None:
        """
        Callback for container crashes.

        Args:
            container_id: Container ID
            exit_code: Container exit code
            crash_details: Crash details
        """
        try:
            # Emit crash notification to all clients
            await self.sio.emit(
                "container_crashed",
                {
                    "container_id": container_id,
                    "exit_code": exit_code,
                    "crash_details": crash_details,
                    "timestamp": asyncio.get_event_loop().time(),
                },
            )

            # Log user activity
            await self.user_logger.log_user_activity(
                "container_crash",
                container_id,
                f"Container crashed with exit code {exit_code}",
                {"exit_code": exit_code, "crash_details": crash_details},
            )

        except Exception as e:
            self.system_logger.log_error(
                e, {"callback": "_on_container_crash", "container_id": container_id}
            )

    async def _on_resource_alert(
        self,
        container_id: str,
        resource_type: str,
        current_value: float,
        threshold: float,
        usage_data: Dict[str, Any],
    ) -> None:
        """
        Callback for resource usage alerts.

        Args:
            container_id: Container ID
            resource_type: Type of resource that exceeded threshold
            current_value: Current resource usage value
            threshold: Threshold that was exceeded
            usage_data: Complete resource usage data
        """
        try:
            # Emit resource alert to all clients
            await self.sio.emit(
                "resource_alert",
                {
                    "container_id": container_id,
                    "resource_type": resource_type,
                    "current_value": current_value,
                    "threshold": threshold,
                    "usage_data": usage_data,
                    "timestamp": asyncio.get_event_loop().time(),
                },
            )

            # Log user activity
            await self.user_logger.log_user_activity(
                "resource_alert",
                container_id,
                f"Resource threshold exceeded: {resource_type} at {current_value:.2f} (threshold: {threshold:.2f})",
                {
                    "resource_type": resource_type,
                    "current_value": current_value,
                    "threshold": threshold,
                },
            )

        except Exception as e:
            self.system_logger.log_error(
                e, {"callback": "_on_resource_alert", "container_id": container_id}
            )

    # Resource monitoring event handlers

    async def handle_get_resource_thresholds(
        self, sid: str, data: Dict[str, Any]
    ) -> None:
        """
        Handle get_resource_thresholds event.

        Args:
            sid: Socket session ID
            data: Event data (empty for this event)
        """
        try:
            self.system_logger.log_socket_event("get_resource_thresholds", sid, data)

            # Get current thresholds
            thresholds = self.container_manager.get_resource_thresholds()

            await self.sio.emit(
                "resource_thresholds",
                {
                    "thresholds": thresholds,
                    "timestamp": asyncio.get_event_loop().time(),
                },
                to=sid,
            )

        except Exception as e:
            await self._emit_error(
                sid,
                "system_error",
                f"Failed to get resource thresholds: {str(e)}",
                data,
            )

    async def handle_set_resource_thresholds(
        self, sid: str, data: Dict[str, Any]
    ) -> None:
        """
        Handle set_resource_thresholds event.

        Args:
            sid: Socket session ID
            data: Event data containing thresholds to set
        """
        try:
            self.system_logger.log_socket_event("set_resource_thresholds", sid, data)

            # Validate required fields
            if "thresholds" not in data:
                await self._emit_error(
                    sid, "validation_error", "Missing 'thresholds' field", data
                )
                return

            thresholds = data["thresholds"]
            if not isinstance(thresholds, dict):
                await self._emit_error(
                    sid, "validation_error", "Thresholds must be a dictionary", data
                )
                return

            # Validate threshold values
            valid_keys = {
                "cpu_percent",
                "memory_percent",
                "disk_read_bytes_per_sec",
                "disk_write_bytes_per_sec",
                "network_rx_bytes_per_sec",
                "network_tx_bytes_per_sec",
            }

            for key, value in thresholds.items():
                if key not in valid_keys:
                    await self._emit_error(
                        sid, "validation_error", f"Invalid threshold key: {key}", data
                    )
                    return

                if not isinstance(value, (int, float)) or value < 0:
                    await self._emit_error(
                        sid,
                        "validation_error",
                        f"Threshold value must be a positive number: {key}",
                        data,
                    )
                    return

            # Set thresholds
            self.container_manager.set_resource_thresholds(thresholds)

            # Get updated thresholds to confirm
            updated_thresholds = self.container_manager.get_resource_thresholds()

            await self.sio.emit(
                "resource_thresholds_updated",
                {
                    "thresholds": updated_thresholds,
                    "timestamp": asyncio.get_event_loop().time(),
                },
                to=sid,
            )

            # Log user activity
            await self.user_logger.log_user_activity(
                "resource_thresholds_updated",
                "system",
                f"Resource thresholds updated",
                {"thresholds": thresholds},
            )

        except Exception as e:
            await self._emit_error(
                sid,
                "system_error",
                f"Failed to set resource thresholds: {str(e)}",
                data,
            )

    async def handle_get_resource_usage_history(
        self, sid: str, data: Dict[str, Any]
    ) -> None:
        """
        Handle get_resource_usage_history event.

        Args:
            sid: Socket session ID
            data: Event data containing container_id and optional limit
        """
        try:
            self.system_logger.log_socket_event("get_resource_usage_history", sid, data)

            # Validate required fields
            if "container_id" not in data:
                await self._emit_error(
                    sid, "validation_error", "Missing 'container_id' field", data
                )
                return

            container_id = data["container_id"]
            limit = data.get("limit", 10)

            if not isinstance(limit, int) or limit < 0:
                await self._emit_error(
                    sid,
                    "validation_error",
                    "Limit must be a non-negative integer",
                    data,
                )
                return

            # Get resource usage history
            history = self.container_manager.get_resource_usage_history(
                container_id, limit
            )

            await self.sio.emit(
                "resource_usage_history",
                {
                    "container_id": container_id,
                    "history": history,
                    "limit": limit,
                    "timestamp": asyncio.get_event_loop().time(),
                },
                to=sid,
            )

        except Exception as e:
            await self._emit_error(
                sid,
                "system_error",
                f"Failed to get resource usage history: {str(e)}",
                data,
            )

    async def handle_enable_resource_monitoring(
        self, sid: str, data: Dict[str, Any]
    ) -> None:
        """
        Handle enable_resource_monitoring event.

        Args:
            sid: Socket session ID
            data: Event data (empty for this event)
        """
        try:
            self.system_logger.log_socket_event("enable_resource_monitoring", sid, data)

            # Enable resource monitoring
            self.container_manager.enable_resource_monitoring()

            await self.sio.emit(
                "resource_monitoring_enabled",
                {
                    "enabled": True,
                    "timestamp": asyncio.get_event_loop().time(),
                },
                to=sid,
            )

            # Log user activity
            await self.user_logger.log_user_activity(
                "resource_monitoring_enabled",
                "system",
                "Resource monitoring enabled",
            )

        except Exception as e:
            await self._emit_error(
                sid,
                "system_error",
                f"Failed to enable resource monitoring: {str(e)}",
                data,
            )

    async def handle_disable_resource_monitoring(
        self, sid: str, data: Dict[str, Any]
    ) -> None:
        """
        Handle disable_resource_monitoring event.

        Args:
            sid: Socket session ID
            data: Event data (empty for this event)
        """
        try:
            self.system_logger.log_socket_event(
                "disable_resource_monitoring", sid, data
            )

            # Disable resource monitoring
            self.container_manager.disable_resource_monitoring()

            await self.sio.emit(
                "resource_monitoring_disabled",
                {
                    "enabled": False,
                    "timestamp": asyncio.get_event_loop().time(),
                },
                to=sid,
            )

            # Log user activity
            await self.user_logger.log_user_activity(
                "resource_monitoring_disabled",
                "system",
                "Resource monitoring disabled",
            )

        except Exception as e:
            await self._emit_error(
                sid,
                "system_error",
                f"Failed to disable resource monitoring: {str(e)}",
                data,
            )
