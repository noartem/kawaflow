"""
Flow Manager Main Application

Integrates all components for comprehensive container lifecycle management
with Socket.IO-based real-time communication and Unix socket integration.
"""

import asyncio
import os
import signal
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI

from container_manager import ContainerManager
from socket_communication_handler import SocketCommunicationHandler
from socket_event_handler import SocketIOEventHandler
from system_logger import SystemLogger
from user_activity_logger import UserActivityLogger


class FlowManagerApp:
    """
    Main application class that integrates all components.

    Provides dependency injection, initialization, and graceful shutdown
    for the complete container lifecycle management system.
    """

    def __init__(self, socket_dir: str = "/tmp/kawaflow/sockets"):
        """
        Initialize the Flow Manager application.

        Args:
            socket_dir: Directory for Unix socket files
        """
        self.socket_dir = socket_dir

        # Initialize logging
        self.system_logger = SystemLogger("flow_manager")

        # Initialize Socket.IO server
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",  # Configure as needed for production
            logger=False,  # Use our custom logging
            engineio_logger=False,
        )

        # Initialize user activity logger
        self.user_logger = UserActivityLogger(self.sio)

        # Initialize core components
        self.container_manager = ContainerManager(socket_dir=socket_dir)
        self.socket_handler = SocketCommunicationHandler(
            socket_dir=socket_dir, logger=self.system_logger
        )

        # Initialize Socket.IO event handler
        self.event_handler = SocketIOEventHandler(
            sio=self.sio,
            container_manager=self.container_manager,
            socket_handler=self.socket_handler,
            system_logger=self.system_logger,
            user_logger=self.user_logger,
        )

        # Application state
        self._shutdown_event = asyncio.Event()
        self._background_tasks = []

        self.system_logger.log_debug(
            "FlowManagerApp initialized", {"socket_dir": socket_dir}
        )

    async def startup(self) -> None:
        """
        Initialize application components and start background tasks.
        """
        try:
            self.system_logger.log_debug("Starting Flow Manager application", {})

            # Ensure socket directory exists
            os.makedirs(self.socket_dir, exist_ok=True)

            # Start container monitoring
            await self.container_manager.start_monitoring()

            # Start background tasks
            self._background_tasks.append(
                asyncio.create_task(self._health_check_loop())
            )

            self.system_logger.log_debug(
                "Flow Manager application started successfully",
                {"background_tasks": len(self._background_tasks)},
            )

        except Exception as e:
            self.system_logger.log_error(
                e, {"operation": "startup", "component": "FlowManagerApp"}
            )
            raise

    async def shutdown(self) -> None:
        """
        Gracefully shutdown application components.
        """
        try:
            self.system_logger.log_debug("Shutting down Flow Manager application", {})

            # Signal shutdown to background tasks
            self._shutdown_event.set()

            # Cancel background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            # Stop container monitoring
            await self.container_manager.stop_monitoring()

            # Close socket connections
            await self.socket_handler.close_all_connections()

            self.system_logger.log_debug(
                "Flow Manager application shutdown complete", {}
            )

        except Exception as e:
            self.system_logger.log_error(
                e, {"operation": "shutdown", "component": "FlowManagerApp"}
            )

    async def _health_check_loop(self) -> None:
        """
        Background task for periodic health checks and maintenance.
        """
        while not self._shutdown_event.is_set():
            try:
                # Perform health checks every 30 seconds
                await asyncio.sleep(30)

                if self._shutdown_event.is_set():
                    break

                # Check container health and emit status updates
                containers = await self.container_manager.list_containers()

                for container in containers:
                    try:
                        status = await self.container_manager.get_container_status(
                            container.id
                        )

                        # Emit status update to all clients
                        await self.sio.emit(
                            "container_status_update",
                            {
                                "container_id": container.id,
                                "status": {
                                    "state": status.state.value,
                                    "health": status.health.value,
                                    "socket_connected": status.socket_connected,
                                    "uptime": str(status.uptime)
                                    if status.uptime
                                    else None,
                                    "resource_usage": status.resource_usage,
                                },
                            },
                        )

                    except Exception as e:
                        self.system_logger.log_error(
                            e,
                            {"operation": "health_check", "container_id": container.id},
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.system_logger.log_error(e, {"operation": "health_check_loop"})
                # Continue the loop even if individual checks fail
                await asyncio.sleep(5)


# Global application instance
app_instance = FlowManagerApp()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown.
    """
    # Startup
    await app_instance.startup()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        asyncio.create_task(app_instance.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        yield
    finally:
        # Shutdown
        await app_instance.shutdown()


# Create FastAPI application with integrated Socket.IO
app = FastAPI(
    title="Flow Manager",
    description="Container lifecycle management with Socket.IO integration",
    version="1.0.0",
    lifespan=lifespan,
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "flow-manager",
        "socket_dir": app_instance.socket_dir,
        "components": {
            "container_manager": "active",
            "socket_handler": "active",
            "event_handler": "active",
        },
    }


# Mount Socket.IO ASGI app
socket_app = socketio.ASGIApp(app_instance.sio, other_asgi_app=app)


# Export the socket app as the main ASGI application
app = socket_app


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info",
    )
