import socket


def get_machine_uuid():
    return socket.gethostname()
