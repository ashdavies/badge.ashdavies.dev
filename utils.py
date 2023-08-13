import socket
import os


def check_socket(host: str, port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection = sock.connect_ex((host, port))
    try:
        if connection != 0:
            raise Exception(f"Socket connection failed for port {port}")
    finally:
        sock.close()


def check_path(path: str):
    if not os.path.exists(path):
        os.makedirs(path)
