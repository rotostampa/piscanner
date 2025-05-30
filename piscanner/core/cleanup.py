import asyncio

from piscanner.utils.storage import cleanup_db


async def start_cleanup(verbose, sleep_duration=3600, seconds=86400):

    count = await cleanup_db(seconds=seconds)

    if verbose or count > 0:
        print(f"🧹 Deleted {count} records")

    await asyncio.sleep(sleep_duration)


def cleanup_coroutines(*args, **opts):
    yield start_cleanup, args, opts
