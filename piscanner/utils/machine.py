import socket
import platform

is_mac = platform.system() == "Darwin"


def get_machine_uuid():
    return socket.gethostname()
