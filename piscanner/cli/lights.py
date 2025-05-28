import asyncio
import click

from piscanner.utils.lights import (
    setup_gpio,
    cleanup_gpio,
    flash_green,
    flash_red,
    flash_yellow,
)


async def test_lights(**opts):
    while True:
        for func in (flash_red, flash_green, flash_yellow):
            await func(**opts, verbose=True)


@click.command(help="Test wait")
@click.option("--duration", default="0.2", type=float, help="Time to wait for")
@click.option("--wait", default="0.2", type=float, help="Time to wait for")
def lights(duration, wait):

    setup_gpio()
    asyncio.run(test_lights(duration=duration, wait=wait))
    cleanup_gpio()
