import time

import click
import asyncio
from piscanner.utils.storage import init, insert_barcode


async def populate_initial_data():
    await init()

    for i in range(10):
        await insert_barcode('44Xtest{}'.format(i + 1))

@click.command(help="Populate with initial data")
def populate():
    asyncio.run(populate_initial_data())
