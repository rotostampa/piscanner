import ipaddress
import platform
import socket

is_mac = platform.system() == "Darwin"


def get_hostname():
    return socket.gethostname()


def is_ipv4(s):
    try:
        return isinstance(ipaddress.ip_address(s), ipaddress.IPv4Address)
    except ValueError:
        return False


def get_local_hostname():
    hostname = get_hostname()

    if hostname.endswith(".local") or is_ipv4(hostname):
        return hostname
    else:
        return "{}.local".format(hostname)
