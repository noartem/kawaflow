import asyncio
import docker
from docker import errors
import os
import shutil
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn

# --- Configuration ---
FLOW_BASE_DIR = "/tmp/kawaflow"
SOCKET_FILE_NAME = "flow.sock"
MAIN_PY_FILE_NAME = "main.py"
TEMPLATE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "main.py.template")
)
DOCKER_IMAGE = "flow"  # Aligned with flow/Taskfile.yml
INACTIVITY_TIMEOUT = 60  # seconds
CONTAINER_APP_DIR = "/app"


# --- Data Models ---
class CreateFlowRequest(BaseModel):
    flow_id: str
    script: str


# --- Flow Manager Class ---
class FlowManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.active_flows = {}  # {flow_id: {"container": container, "last_active": timestamp}}

    async def create_flow(self, flow_id: str, script_content: str):
        """
        Creates and starts a new flow container.
        """
        if flow_id in self.active_flows:
            await self.stop_flow(flow_id)

        flow_dir = os.path.join(FLOW_BASE_DIR, flow_id)
        script_path_host = os.path.join(flow_dir, MAIN_PY_FILE_NAME)
        socket_path_container = os.path.join(CONTAINER_APP_DIR, SOCKET_FILE_NAME)

        os.makedirs(flow_dir, exist_ok=True)

        with open(TEMPLATE_PATH, "r") as f:
            template = f.read()
        script = template.replace("{{ FILE }}", script_content)
        with open(script_path_host, "w") as f:
            f.write(script)

        print(f"Starting container for flow {flow_id}...")
        container = self.docker_client.containers.run(
            DOCKER_IMAGE,
            detach=True,
            auto_remove=True,
            name=f"kawaflow-{flow_id}",
            volumes={flow_dir: {"bind": CONTAINER_APP_DIR, "mode": "rw"}},
            environment={"SOCKET_PATH": socket_path_container},
        )

        self.active_flows[flow_id] = {
            "container": container,
            "last_active": asyncio.get_event_loop().time(),
        }
        print(f"Flow {flow_id} created with container ID {container.id[:12]}.")
        return {"status": "created", "flow_id": flow_id}

    async def stop_flow(self, flow_id: str):
        """
        Stops and cleans up a flow container.
        """
        if flow_id not in self.active_flows:
            print(f"Stop requested for non-existent flow ID '{flow_id}'. Ignoring.")
            return {"status": "not_found", "flow_id": flow_id}

        print(f"Stopping container for flow {flow_id}...")
        container = self.active_flows[flow_id]["container"]

        try:
            container.stop(timeout=5)
            print(f"Container for flow {flow_id} stopped.")
        except errors.NotFound:
            print(f"Container for flow {flow_id} not found, likely already stopped.")
        except Exception as e:
            print(f"Error stopping container for flow {flow_id}: {e}")

        flow_dir = os.path.join(FLOW_BASE_DIR, flow_id)
        if os.path.exists(flow_dir):
            shutil.rmtree(flow_dir)
            print(f"Cleaned up directory: {flow_dir}")

        del self.active_flows[flow_id]
        print(f"Flow {flow_id} stopped and cleaned up.")
        return {"status": "stopped", "flow_id": flow_id}

    async def send_command_to_flow(self, flow_id: str, command: str):
        if flow_id not in self.active_flows:
            raise ValueError(f"Flow with ID '{flow_id}' not found.")

        socket_path = os.path.join(FLOW_BASE_DIR, flow_id, SOCKET_FILE_NAME)

        # Wait for the socket to be created by the container
        for _ in range(10):
            if os.path.exists(socket_path):
                break
            await asyncio.sleep(0.5)
        else:
            raise FileNotFoundError(f"Socket file not found for flow {flow_id}")

        reader, writer = await asyncio.open_unix_connection(socket_path)

        print(f"Sending command '{command}' to flow {flow_id}")
        writer.write(command.encode())
        await writer.drain()

        data = await reader.read(4096)
        writer.close()
        await writer.wait_closed()

        response = json.loads(data.decode())

        # Update activity timestamp
        self.active_flows[flow_id]["last_active"] = asyncio.get_event_loop().time()

        return response

    async def _monitor_inactivity(self):
        """
        Periodically checks for inactive flows and stops them.
        """
        while True:
            await asyncio.sleep(10)
            now = asyncio.get_event_loop().time()
            inactive_flows = []
            for flow_id, data in list(self.active_flows.items()):
                if now - data["last_active"] > INACTIVITY_TIMEOUT:
                    inactive_flows.append(flow_id)

            for flow_id in inactive_flows:
                print(f"Flow {flow_id} is inactive. Stopping.")
                await self.stop_flow(flow_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.flow_manager = FlowManager()
    loop = asyncio.get_event_loop()
    monitor_task = loop.create_task(app.state.flow_manager._monitor_inactivity())

    yield

    # Shutdown
    monitor_task.cancel()


# --- FastAPI App ---
app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    flow_manager = websocket.app.state.flow_manager
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            payload = data.get("payload", {})
            response = None

            try:
                if action == "create":
                    response = await flow_manager.create_flow(
                        flow_id=payload.get("flow_id"),
                        script_content=payload.get("script"),
                    )
                elif action == "stop":
                    response = await flow_manager.stop_flow(
                        flow_id=payload.get("flow_id")
                    )
                elif action == "send_command":
                    response = await flow_manager.send_command_to_flow(
                        flow_id=payload.get("flow_id"), command=payload.get("command")
                    )
                else:
                    response = {"error": "Unknown action"}
            except Exception as e:
                response = {"error": str(e)}

            await websocket.send_json(response)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")


# A simple endpoint to check if the server is running
@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    # This is for local development.
    # In production, you'd use a proper ASGI server like Gunicorn with Uvicorn workers.
    uvicorn.run(app, host="0.0.0.0", port=8000)