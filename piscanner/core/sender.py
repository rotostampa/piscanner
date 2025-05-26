import asyncio


async def start_sender(verbose):
    while True:
        await asyncio.sleep(1)
        if verbose:
            print("📤 Sender is running...")


def sender_coroutines(*args, **opts):
    yield start_sender, args, opts
