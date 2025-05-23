import aiosqlite
import time
import asyncio

import os
import uuid

db_lock = asyncio.Lock()


DB_FILE = os.path.join(os.path.expanduser("~"), "piscanner-v3.db")


async def init():
    async with db_lock:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS barcodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT NOT NULL,
                    create_timestamp REAL NOT NULL,
                    uploaded_timestamp REAL
                )
                """
            )
            await db.commit()


async def insert_barcode(barcode: str):
    async with db_lock:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "INSERT INTO barcodes (barcode, create_timestamp) VALUES (?, ?)",
                (barcode, time.time()),
            )
            await db.commit()


async def read(limit=50):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT id, barcode, create_timestamp, uploaded_timestamp FROM barcodes ORDER BY create_timestamp DESC LIMIT ?",
            (limit,),
        )
        return await cursor.fetchall()
