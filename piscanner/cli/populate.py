import click
import asyncio
from piscanner.utils.storage import init, insert_barcode, cleanup_db

import random
import string


def barcode(prefix):
    return "{}X{}".format(
        prefix, "".join(random.choices(string.ascii_letters, k=8)).lower()
    )


async def log_insert(value):
    print(value)
    return await insert_barcode(value)


async def populate_initial_data(barcodes):
    await init()

    if barcodes:
        # Insert provided barcodes verbatim
        for code in barcodes:
            await log_insert(code)
    else:
        # Generate random barcodes as before
        for i in range(10):
            await log_insert(barcode("44"))

        for i in range(3):
            await log_insert(barcode(prefix="4{}".format(i)))

        await log_insert(barcode(prefix="INVALID"))
        await log_insert(barcode(prefix="INVALID"))


async def cleanup_database(seconds):
    await init()
    return await cleanup_db(seconds)


@click.command(help="Populate with initial data")
@click.argument("barcodes", nargs=-1)
def populate(barcodes):
    # Combine option barcodes and argument barcodes
    asyncio.run(populate_initial_data(barcodes))


@click.command(help="Cleanup old records from the database")
@click.option(
    "--days", default=0, type=int, help="Delete records older than this many days"
)
def cleanup(days):
    seconds = int(days * 86400)  # Convert days to seconds
    deleted = asyncio.run(cleanup_database(seconds))
    click.echo(f"Deleted {deleted} records older than {days} days")
