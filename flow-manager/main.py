import socketio
import docker
from fastapi import FastAPI

app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi")


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


@sio.on("start_container")
async def start_container(sid, data):
    image = data.get("image")
    if not image:
        await sio.emit("error", {"message": "Image name is required"}, to=sid)
        return

    try:
        client = docker.from_env()
        container = client.containers.run(image, detach=True)
        await sio.emit(
            "container_started",
            {"id": container.id, "name": container.name},
            to=sid,
        )
    except docker.errors.ImageNotFound:
        await sio.emit("error", {"message": f"Image '{image}' not found"}, to=sid)
    except Exception as e:
        await sio.emit("error", {"message": str(e)}, to=sid)


@sio.on("stop_container")
async def stop_container(sid, data):
    container_id = data.get("container_id")
    if not container_id:
        await sio.emit("error", {"message": "Container ID is required"}, to=sid)
        return

    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop()
        await sio.emit("container_stopped", {"id": container.id}, to=sid)
    except docker.errors.NotFound:
        await sio.emit(
            "error", {"message": f"Container '{container_id}' not found"}, to=sid
        )
    except Exception as e:
        await sio.emit("error", {"message": str(e)}, to=sid)


app.mount("/", socketio.ASGIApp(sio))
