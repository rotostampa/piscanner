import socket
import platform

is_mac = platform.system() == "Darwin"


def get_hostname():
    return socket.gethostname()
