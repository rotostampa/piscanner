import asyncio


async def start_sender():
    while True:
        await asyncio.sleep(1)
        print("Sender is running...")


def sender_coroutines(*args, **opts):
    yield start_sender, args, opts
