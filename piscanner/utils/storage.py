import aiosqlite
import time

import os

DB_FILE = os.path.join(os.path.expanduser("~"), "piscanner.db")


async def init():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS barcodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT,
                create_timestamp INTEGER,
                uploaded_timestamp INTEGER
            )
        """
        )
        await db.commit()


async def insert_barcode(barcode: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO barcodes (barcode, create_timestamp, uploaded_timestamp) VALUES (?, ?, ?)",
            (barcode, int(time.time()), None),
        )
        await db.commit()


async def read():
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT id, barcode, create_timestamp, uploaded_timestamp FROM barcodes ORDER BY create_timestamp DESC LIMIT 50"
        )
        rows = await cursor.fetchall()
        return rows
