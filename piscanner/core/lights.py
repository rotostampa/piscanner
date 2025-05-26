import asyncio

from piscanner.utils.storage import unsent_events_count
from piscanner.utils.lights import flash_green, flash_red


async def start_lights(verbose=False):
    while True:
        await asyncio.sleep(1)

        count = await unsent_events_count()

        if verbose:
            print("💡 Uncounted events:", count)

        if count == 0:
            await flash_green(verbose=verbose)
        else:
            await flash_red(verbose=verbose)


def lights_coroutines(*args, **opts):
    yield start_lights, args, opts
