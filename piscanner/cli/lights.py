import asyncio
import click

from piscanner.utils.lights import setup_gpio, cleanup_gpio, flash_green, flash_red, flash_yellow


async def test_lights():
    for func in (flash_red, flash_green, flash_yellow):
        await func(duration=1, wait=1, verbose=True)


@click.command(help="Test wait")
@click.option("--duration", default="1", type=int, help="Time to wait for")
@click.option("--wait", default="1", type=int, help="Time to wait for")
def lights(duration, wait):

    setup_gpio()
    asyncio.run(test_lights())
    cleanup_gpio()
