"""
Socket Communication Handler for container communication via Unix sockets.

This module provides the SocketCommunicationHandler class that manages
bidirectional communication with flow containers through Unix socket files.
Each container has a dedicated socket file named {container_id}.sock.
"""

import asyncio
import json
import socket
from pathlib import Path
from typing import Dict

from system_logger import SystemLogger


class SocketCommunicationError(Exception):
    """Exception raised for socket communication errors."""

    pass


class SocketTimeoutError(SocketCommunicationError):
    """Exception raised when socket operations timeout."""

    pass


class SocketConnectionError(SocketCommunicationError):
    """Exception raised when socket connection fails."""

    pass


class SocketCommunicationHandler:
    def __init__(
        self,
        logger: SystemLogger,
        socket_dir: str = "/tmp/kawaflow/sockets",
    ):
        self.socket_dir = Path(socket_dir)
        self.socket_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger

        # Track active socket connections
        self._connections: Dict[str, socket.socket] = {}
        self._connection_status: Dict[str, bool] = {}

        self.logger.debug(
            "initialized",
            {"socket_dir": str(self.socket_dir)},
        )

    def _get_socket_path(self, container_id: str) -> Path:
        """Get the socket file path for a container."""
        return self.socket_dir / f"{container_id}.sock"

    async def setup_socket(self, container_id: str) -> None:
        """
        Set up Unix socket for container communication.

        Args:
            container_id: ID of the container to set up socket for

        Raises:
            SocketConnectionError: If socket setup fails
        """
        try:
            socket_path = self._get_socket_path(container_id)

            # Remove existing socket file if it exists
            if socket_path.exists():
                socket_path.unlink()
                self.logger.debug(
                    "Removed existing socket file",
                    {"container_id": container_id, "socket_path": str(socket_path)},
                )

            # Create Unix socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.setblocking(False)

            # Bind to socket path
            sock.bind(str(socket_path))
            sock.listen(1)

            # Store connection
            self._connections[container_id] = sock
            self._connection_status[container_id] = True

            self.logger.debug(
                "Socket setup completed",
                {"container_id": container_id, "socket_path": str(socket_path)},
            )

        except Exception as e:
            self.logger.error(
                e, {"operation": "setup_socket", "container_id": container_id}
            )
            raise SocketConnectionError(
                f"Failed to setup socket for container {container_id}: {str(e)}"
            )

    async def cleanup_socket(self, container_id: str) -> None:
        """
        Clean up Unix socket for container.

        Args:
            container_id: ID of the container to clean up socket for
        """
        try:
            # Close socket connection if exists
            if container_id in self._connections:
                sock = self._connections[container_id]
                sock.close()
                del self._connections[container_id]

            # Remove socket file
            socket_path = self._get_socket_path(container_id)
            if socket_path.exists():
                socket_path.unlink()
                self.logger.debug(
                    "Removed socket file",
                    {"container_id": container_id, "socket_path": str(socket_path)},
                )

            # Update connection status
            self._connection_status[container_id] = False

            self.logger.debug(
                "Socket cleanup completed", {"container_id": container_id}
            )

        except Exception as e:
            self.logger.error(
                e, {"operation": "cleanup_socket", "container_id": container_id}
            )
            # Don't raise exception for cleanup operations

    def is_socket_connected(self, container_id: str) -> bool:
        """
        Check if socket is connected for a container.

        Args:
            container_id: ID of the container to check

        Returns:
            True if socket is connected, False otherwise
        """
        return self._connection_status.get(container_id, False)

    async def send_message(self, container_id: str, message: dict) -> None:
        """
        Send message to container via Unix socket.

        Args:
            container_id: ID of the container to send message to
            message: Message dictionary to send

        Raises:
            SocketConnectionError: If socket is not connected
            SocketCommunicationError: If message sending fails
        """
        if not self.is_socket_connected(container_id):
            raise SocketConnectionError(
                f"Socket not connected for container {container_id}"
            )

        try:
            # Serialize message to JSON
            message_data = json.dumps(message).encode("utf-8")
            message_length = len(message_data)

            # Get socket connection
            sock = self._connections.get(container_id)
            if not sock:
                raise SocketConnectionError(
                    f"No socket connection for container {container_id}"
                )

            # Accept connection if needed (for server socket)
            try:
                client_sock, _ = await asyncio.get_event_loop().run_in_executor(
                    None, sock.accept
                )
            except Exception:
                # If accept fails, assume we're already connected
                client_sock = sock

            # Send message length first (4 bytes)
            length_bytes = message_length.to_bytes(4, byteorder="big")
            await asyncio.get_event_loop().run_in_executor(
                None, client_sock.send, length_bytes
            )

            # Send message data
            await asyncio.get_event_loop().run_in_executor(
                None, client_sock.send, message_data
            )

            self.logger.communication(container_id, "sent", message)

        except Exception as e:
            self.logger.error(
                e,
                {
                    "operation": "send_message",
                    "container_id": container_id,
                    "message": message,
                },
            )
            raise SocketCommunicationError(
                f"Failed to send message to container {container_id}: {str(e)}"
            )

    async def receive_message(self, container_id: str, timeout: int = 30) -> dict:
        """
        Receive message from container via Unix socket.

        Args:
            container_id: ID of the container to receive message from
            timeout: Timeout in seconds for receiving message

        Returns:
            Received message as dictionary

        Raises:
            SocketConnectionError: If socket is not connected
            SocketTimeoutError: If receive operation times out
            SocketCommunicationError: If message receiving fails
        """
        if not self.is_socket_connected(container_id):
            raise SocketConnectionError(
                f"Socket not connected for container {container_id}"
            )

        try:
            # Get socket connection
            sock = self._connections.get(container_id)
            if not sock:
                raise SocketConnectionError(
                    f"No socket connection for container {container_id}"
                )

            # Accept connection if needed (for server socket)
            try:
                client_sock, _ = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, sock.accept),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                raise SocketTimeoutError(
                    f"Timeout waiting for connection from container {container_id}"
                )
            except Exception:
                # If accept fails, assume we're already connected
                client_sock = sock

            # Receive message length first (4 bytes)
            try:
                length_bytes = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, client_sock.recv, 4),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                raise SocketTimeoutError(
                    f"Timeout receiving message length from container {container_id}"
                )

            if len(length_bytes) != 4:
                raise SocketCommunicationError(
                    f"Invalid message length received from container {container_id}"
                )

            message_length = int.from_bytes(length_bytes, byteorder="big")

            # Receive message data
            try:
                message_data = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, client_sock.recv, message_length
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                raise SocketTimeoutError(
                    f"Timeout receiving message data from container {container_id}"
                )

            if len(message_data) != message_length:
                raise SocketCommunicationError(
                    f"Incomplete message received from container {container_id}"
                )

            # Deserialize message from JSON
            try:
                message = json.loads(message_data.decode("utf-8"))
            except json.JSONDecodeError as e:
                raise SocketCommunicationError(
                    f"Invalid JSON message from container {container_id}: {str(e)}"
                )

            self.logger.communication(container_id, "received", message)

            return message

        except (SocketTimeoutError, SocketConnectionError, SocketCommunicationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            self.logger.error(
                e,
                {
                    "operation": "receive_message",
                    "container_id": container_id,
                    "timeout": timeout,
                },
            )
            raise SocketCommunicationError(
                f"Failed to receive message from container {container_id}: {str(e)}"
            )

    async def close_all_connections(self) -> None:
        """Close all active socket connections."""
        for container_id in list(self._connections.keys()):
            await self.cleanup_socket(container_id)

        self.logger.debug("All socket connections closed", {})
