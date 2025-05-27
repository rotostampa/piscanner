import aiosqlite
import time
import datetime
import asyncio
from piscanner.utils.machine import is_mac
import os
from itertools import repeat
from piscanner.utils.datastructures import data

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
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS barcodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT NOT NULL,
                    created_timestamp REAL NOT NULL,
                    uploaded_timestamp REAL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY NOT NULL,
                    value TEXT NOT NULL,
                    create_timestamp REAL NOT NULL
                );
                """
            )

            # Set default settings while we still have the connection and lock

            # Use the existing connection for setting defaults
            await _set_setting_internal(
                settings_dict={
                    "PISCANNER_SERVER_TOKEN": "",
                    "PISCANNER_SERVER_HOST": "https://rotostampa.com",
                    "PISCANNER_SERVER_STEP": "0",
                },
                overwrite_settings=False,
                db_connection=db
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
        yield data(
            id= id,
            barcode= barcode,
            created_timestamp= time_to_date(created_timestamp),
            uploaded_timestamp= time_to_date(uploaded_timestamp),
        )

    await db.close()


async def unsent_events_count(seconds=5):
    """
    Check if there are any records without an uploaded_timestamp.

    Args:
        seconds: Number of seconds from now to filter out recently created records (default: 5)

    Returns:
        int: Number of unsent records
    """
    cutoff_time = timestamp(seconds)  # Negative seconds to exclude recent records

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM barcodes
            WHERE uploaded_timestamp IS NULL
            AND created_timestamp <= ?
            """,
            (cutoff_time,),
        )
        count = await cursor.fetchone()
        return count[0]

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
            await db.commit()
            return cursor.rowcount


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
            await db.commit()
            return cursor.rowcount


async def get_settings():
    """
    Get all settings.

    Returns:
        dict: Dictionary of all settings (key-value pairs)
    """
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT key, value FROM settings ORDER BY key")

        settings = data()
        async for key, value in cursor:
            settings[key] = value

        return settings


async def _set_setting_internal(settings_dict, db_connection, overwrite_settings = True):
    """
    Internal helper function to set settings using an existing connection.

    Args:
        settings_dict: Dictionary of settings to set
        overwrite_settings: Whether to overwrite existing settings
        db_connection: Database connection to use

    Returns:
        int: Number of records updated/inserted
    """
    if not settings_dict:
        return 0

    current_time = timestamp()
    placeholders = ",".join(repeat("(?, ?, ?)", len(settings_dict)))
    params = tuple(
        param
        for key, value in settings_dict.items()
        for param in (key, value, current_time)
    )

    if overwrite_settings:
        # If overwrite is enabled, update existing settings
        cursor = await db_connection.execute(
            f"""
            INSERT INTO settings (key, value, create_timestamp)
            VALUES {placeholders}
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                create_timestamp = excluded.create_timestamp
            """,
            params,
        )
    else:
        # If overwrite is disabled, ignore conflicts (keep existing settings)
        cursor = await db_connection.execute(
            f"""
            INSERT INTO settings (key, value, create_timestamp)
            VALUES {placeholders}
            ON CONFLICT(key) DO NOTHING
            """,
            params,
        )
    return cursor.rowcount


async def set_setting(**settings_dict):
    """
    Set multiple settings at once.

    Args:
        settings_dict: Dictionary of settings (key-value pairs) to set in the database
        overwrite_settings: If True, existing settings will be updated; if False, existing settings will be kept

    Returns:
        int: Number of records updated/inserted
    """
    if not settings_dict:
        return 0

    async with db_lock:
        async with aiosqlite.connect(DB_FILE) as db:
            result = await _set_setting_internal(
                settings_dict=settings_dict,
                overwrite_settings=True,
                db_connection=db
            )
            await db.commit()
            return result
