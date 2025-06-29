import socket
import os
from kawa.module import Module
from kawa.utils import json_encode

SOCKET_PATH = "/var/run/kawaflow.sock"

def handle_command(command: str, module: Module):
    if command == "dump":
        return module.dump()
    return {"error": "unknown command"}

def main():
    module = Module("main.py")

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
                response = handle_command(command, module)
                conn.sendall(json_encode(response).encode())

if __name__ == "__main__":
    main()
