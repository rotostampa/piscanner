import json
from datetime import datetime


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that automatically converts datetime objects to ISO format strings.

    Usage:
        # Direct use
        json_string = json.dumps(data, cls=DateTimeEncoder)

        # With aiohttp
        async with aiohttp.ClientSession(json_serialize=dumps) as session:
            await session.post(url, json=data)
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def dumps(obj):
    """
    Serialize an object to JSON string with datetime support.

    Args:
        obj: The Python object to serialize

    Returns:
        str: JSON string representation of the object
    """
    return json.dumps(obj, cls=DateTimeEncoder)


def loads(json_string):
    """
    Parse a JSON string into a Python object.

    This is a simple wrapper around json.loads() for API symmetry,
    but could be extended in the future to handle custom parsing.

    Args:
        json_string (str): The JSON string to parse

    Returns:
        The parsed Python object
    """
    return json.loads(json_string)
