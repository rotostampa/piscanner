import asyncio
import datetime

from piscanner.utils.lights import flash_green, flash_red, flash_yellow
from piscanner.utils.storage import read
from piscanner.core.server import is_success, is_recent


async def start_lights(check_seconds=1, wait_timout=1, verbose=False):
    while True:

        record = None

        async for record in read(limit=1):
            pass

        if record:

            if not record.completed_timestamp:
                await flash_yellow()

            if is_success(record.status):
                await flash_green()
            else:
                await flash_red()
        else:
            await flash_yellow()

        # Wait before checking again
        await asyncio.sleep(wait_timout)


def lights_coroutines(*args, **opts):
    yield start_lights, args, opts
