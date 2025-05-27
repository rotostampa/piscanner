import click
import asyncio
from piscanner.utils.storage import init, insert_barcode, cleanup_db

import random
import string


def barcode(prefix='44'):
    return "{}X{}".format(prefix, "".join(random.choices(string.ascii_letters, k=8)).lower())


async def populate_initial_data():
    await init()

    for i in range(10):
        await insert_barcode(barcode())

    for i in range(3):
        await insert_barcode(barcode(prefix = '4{}'.format(i)))

    await insert_barcode(barcode(prefix = 'TEST'))
    await insert_barcode(barcode(prefix = 'DELTA'))

async def cleanup_database(seconds):
    await init()
    return await cleanup_db(seconds)


@click.command(help="Populate with initial data")
def populate():
    asyncio.run(populate_initial_data())


@click.command(help="Cleanup old records from the database")
@click.option(
    "--days", default=0, type=float, help="Delete records older than this many days"
)
def cleanup(days):
    seconds = int(days * 86400)  # Convert days to seconds
    deleted = asyncio.run(cleanup_database(seconds))
    click.echo(f"Deleted {deleted} records older than {days} days")
