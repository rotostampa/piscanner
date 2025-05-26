import asyncio
from piscanner.utils.storage import read
from piscanner.utils.machine import get_hostname



async def start_sender():
    while True:
        await asyncio.sleep(1)
        print("Sender is running...")


def sender_coroutines():
    yield start_sender, (), {}
