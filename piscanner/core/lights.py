import asyncio
import datetime

from piscanner.utils.lights import flash_green, flash_red, flash_yellow
from piscanner.utils.storage import get_latest_timestamp


async def start_lights(check_seconds=5, wait_timout=5, verbose=False):
    while True:
        # Get the latest timestamp
        latest_timestamp = await get_latest_timestamp()

        if not latest_timestamp or latest_timestamp <= (
            datetime.datetime.now(datetime.UTC)
            - datetime.timedelta(seconds=check_seconds)
        ):
            if verbose:
                print("💡 flashing status lights")


            await flash_red(wait=0, duration=0.1)
            await flash_yellow(wait=0, duration=0.1)
            await flash_green(wait=0, duration=0.1)

        elif verbose:
            print("💡 not flashing ")

        # Wait before checking again
        await asyncio.sleep(wait_timout)


def lights_coroutines(*args, **opts):
    yield start_lights, args, opts
