import aiosqlite
import time
import datetime
import asyncio
from piscanner.utils.machine import is_mac
import os
from itertools import repeat

db_lock = asyncio.Lock()

DB_FILE = "piscanner-v5.db"

if is_mac:
    DB_FILE = os.path.join(os.path.dirname(__file__), DB_FILE)
else:
    DB_FILE = os.path.join(os.path.expanduser("~"), DB_FILE)


def time_to_date(t):
    if t:
        return datetime.datetime.fromtimestamp(t / 1000000)


def timestamp(seconds=0):
    return (time.time() - seconds) * 1000000


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


async def read(limit=50, not_uploaded_only=False):
    """
    Read records from the database.

    Args:
        limit: Maximum number of records to return (default: 50)
        not_uploaded_only: If True, only return records where uploaded_timestamp is NULL (default: False)

    Returns:
        Generator yielding record dictionaries
    """
    db = await aiosqlite.connect(DB_FILE)

    query = "SELECT id, barcode, created_timestamp, uploaded_timestamp FROM barcodes"

    if not_uploaded_only:
        query += " WHERE uploaded_timestamp IS NULL"

    query += " ORDER BY created_timestamp DESC LIMIT ?"

    cursor = await db.execute(
        query,
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


async def unsent_events_count():
    """
    Check if there are any records without an uploaded_timestamp.

    Args:
        seconds: Number of seconds from now to filter out recently created records (default: 5)

    Returns:
        int: Number of unsent records
    """

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM barcodes
            WHERE uploaded_timestamp IS NULL
            """,
        )
        count = await cursor.fetchone()
        return count[0]


async def has_unsent_events(seconds=5):
    """
    Check if there are any records without an uploaded_timestamp.

    Args:
        seconds: Number of seconds from now to filter out recently created records (default: 5)

    Returns:
        bool: True if there are unsent records, False otherwise
    """
    count = await unsent_events_count(seconds)
    return count > 0


async def cleanup_db(seconds=86400):
    """
    Delete records older than the specified number of seconds.

    Args:
        seconds: Number of seconds to keep records for (default: 86400 - one day)
                Records created before now - seconds will be deleted

    Returns:
        int: Number of records deleted
    """
    cutoff_time = timestamp(seconds)  # Negative seconds to go back in time

    async with db_lock:
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute(
                "DELETE FROM barcodes WHERE created_timestamp < ?", (cutoff_time,)
            )
            deleted_count = cursor.rowcount
            await db.commit()
            return deleted_count


async def mark_as_uploaded(record_ids):
    """
    Mark the specified records as uploaded by setting their uploaded_timestamp.

    Args:
        record_ids: List of record IDs to mark as uploaded

    Returns:
        int: Number of records updated
    """
    if not record_ids:
        return 0

    current_time = timestamp()

    # Create placeholders for the SQL query using itertools.repeat
    placeholders = ",".join(repeat("?", len(record_ids)))

    async with db_lock:
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute(
                f"UPDATE barcodes SET uploaded_timestamp = ? WHERE id IN ({placeholders})",
                (current_time, *record_ids),
            )
            updated_count = cursor.rowcount
            await db.commit()
            return updated_count
