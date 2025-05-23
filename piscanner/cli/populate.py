import click
import asyncio
from piscanner.utils.storage import init, insert_barcode

import random
import string


def barcode():
    return "44X{}".format("".join(random.choices(string.ascii_letters, k=8)).lower())


async def populate_initial_data():
    await init()

    for i in range(10):
        await insert_barcode(barcode())


@click.command(help="Populate with initial data")
def populate():
    asyncio.run(populate_initial_data())
