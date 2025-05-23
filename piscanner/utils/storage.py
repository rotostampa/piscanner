import aiosqlite
import time
import datetime
import asyncio
from piscanner.utils.machine import is_mac
import os

db_lock = asyncio.Lock()

DB_FILE = "piscanner-v5.db"

if is_mac:
    DB_FILE = os.path.join(os.path.dirname(__file__), DB_FILE)
else:
    DB_FILE = os.path.join(os.path.expanduser("~"), DB_FILE)


def time_to_date(t):
    if t:
        return datetime.datetime.fromtimestamp(t / 1000000)


def timestamp():
    return time.time() * 1000000


async def init():
    async with db_lock:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS barcodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT NOT NULL,
                    created_timestamp REAL NOT NULL,
                    uploaded_timestamp REAL
                )
                """
            )
            await db.commit()


async def insert_barcode(barcode: str):
    async with db_lock:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "INSERT INTO barcodes (barcode, created_timestamp) VALUES (?, ?)",
                (barcode, timestamp()),
            )
            await db.commit()


async def read(limit=50):
    db = await aiosqlite.connect(DB_FILE)
    cursor = await db.execute(
        "SELECT id, barcode, created_timestamp, uploaded_timestamp FROM barcodes ORDER BY created_timestamp DESC LIMIT ?",
        (limit,),
    )
    async for id, barcode, created_timestamp, uploaded_timestamp in cursor:
        yield {
            "id": id,
            "barcode": barcode,
            "created_timestamp": time_to_date(created_timestamp),
            "uploaded_timestamp": time_to_date(uploaded_timestamp),
        }

    await db.close()
