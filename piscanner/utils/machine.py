import uuid
from functools import cache

@cache
def get_machine_uuid():
    with open('/etc/machine-id') as f:
        return uuid.UUID(hex = f.read().strip())
