import click
import asyncio
from piscanner.utils.storage import init, insert_barcode, cleanup_db

import random
import string


def barcode():
    return "44X{}".format("".join(random.choices(string.ascii_letters, k=8)).lower())


async def populate_initial_data():
    await init()

    for i in range(10):
        await insert_barcode(barcode())


async def cleanup_database(seconds):
    await init()
    return await cleanup_db(seconds)


@click.command(help="Populate with initial data")
def populate():
    asyncio.run(populate_initial_data())


@click.command(help="Cleanup old records from the database")
@click.option(
    "--days", default=1, type=float, help="Delete records older than this many days"
)
def cleanup(days):
    seconds = int(days * 86400)  # Convert days to seconds
    deleted = asyncio.run(cleanup_database(seconds))
    click.echo(f"Deleted {deleted} records older than {days} days")
