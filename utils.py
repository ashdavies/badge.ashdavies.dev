import socket
import os


def check_certificate(cert_file: str, key_file: str):
    if not os.path.exists(cert_file):
        raise Exception(f"Certificate file {cert_file} does not exist")

    elif not os.path.exists(key_file):
        raise Exception(f"Key file {key_file} does not exist")


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
