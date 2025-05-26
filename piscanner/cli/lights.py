import asyncio
import click
import time

from piscanner.utils.lights import setup_gpio, cleanup_gpio, flash_green, flash_red


@click.command(help="Test wait")
@click.option("--duration", default="1", type=int, help="Time to wait for")
@click.option("--wait", default="1", type=int, help="Time to wait for")
def alert(duration, wait):

    setup_gpio()
    asyncio.run(flash_red(duration=duration, wait=wait, verbose = True))
    cleanup_gpio()


@click.command(help="Test wait")
@click.option("--duration", default="1", type=int, help="Time to wait for")
@click.option("--wait", default="1", type=int, help="Time to wait for")
def success(duration, wait):

    setup_gpio()
    asyncio.run(flash_green(duration=duration, wait=wait, verbose = True))
    cleanup_gpio()


@click.command(help="Test wait")
def cleanup():

    print("setup")
    setup_gpio()
    time.sleep(1)
    print("cleanup")
    cleanup_gpio()
