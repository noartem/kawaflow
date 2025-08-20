import socket
import os

from kawa import registry
from kawa.utils import json_encode

SOCKET_PATH = os.environ.get("SOCKET_PATH", "/var/run/kawaflow.sock")


def handle_command(command: str):
    if command == "dump":
        return registry.dump()
    return {"error": "unknown command"}


def serve():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(SOCKET_PATH)
        server.listen()
        print(f"Listening on {SOCKET_PATH}")
        conn, addr = server.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                command = data.decode().strip()
                response = handle_command(command)
                conn.sendall(json_encode(response).encode())
