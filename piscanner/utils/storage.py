import aiosqlite
import datetime
from datetime import timezone
import asyncio
from piscanner.utils.machine import is_mac
import os
from itertools import repeat
from piscanner.utils.datastructures import data
from contextlib import asynccontextmanager


DB_FILE = "piscanner-v6.db"

if is_mac:
    DB_FILE = os.path.join(os.path.dirname(__file__), DB_FILE)
else:
    DB_FILE = os.path.join(os.path.expanduser("~"), DB_FILE)


@asynccontextmanager
async def db_transaction(path=DB_FILE, lock=asyncio.Lock()):
    """
    Async context manager that acquires the database lock, connects to the database,
    and automatically commits the transaction when exiting the context.

    Usage:
        async with db_transaction() as db:
            await db.execute("INSERT INTO table VALUES (?)", (value,))
    """
    async with lock:
        async with db_readonly(path=path) as db:
            try:
                yield db
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise e


@asynccontextmanager
async def db_readonly(path=DB_FILE):
    """
    Async context manager that connects to the database in read-only mode
    without acquiring the lock or committing changes.

    Use this for read-only operations that don't modify the database.

    Usage:
        async with db_readonly() as db:
            cursor = await db.execute("SELECT * FROM table")
    """
    async with aiosqlite.connect(path) as db:
        yield db


def timestamp_to_datetime(t):
    """
    Convert a UTC timestamp to a datetime in the local timezone.

    Args:
        t: UTC timestamp stored in the database

    Returns:
        datetime: Datetime object in local timezone
    """
    if t:
        # Convert UTC timestamp to datetime with local timezone
        return datetime.datetime.fromtimestamp(
            t, tz=timezone.utc
        ).astimezone()  # Convert to local timezone


def timestamp(seconds=0):
    """
    Get the current UTC timestamp, optionally offset by a number of seconds.

    Args:
        seconds: Number of seconds to subtract from current time

    Returns:
        float: UTC timestamp
    """
    # Get current UTC timestamp
    return datetime.datetime.now(timezone.utc).timestamp() - seconds


async def init():
    async with db_transaction() as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS barcodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                created_timestamp REAL NOT NULL,
                uploaded_timestamp REAL,
                status TEXT NOT NULL DEFAULT 'LOCAL'
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY NOT NULL,
                value TEXT NOT NULL,
                created_timestamp REAL NOT NULL
            );
            """
        )

        # Set default settings while we still have the connection and lock
        # Use the existing connection for setting defaults
        await _set_setting_internal(
            settings_dict={
                "PISCANNER_SERVER_TOKEN": "",
                "PISCANNER_SERVER_HOST": "https://rotostampa.com",
                "PISCANNER_SERVER_PATH": "/api/storage/piscanner-notify-barcode/",
                "PISCANNER_SERVER_STEP": "0",
            },
            overwrite_settings=False,
            db_connection=db,
        )


async def insert_barcode(barcode: str, status: str = "LOCAL"):
    async with db_transaction() as db:
        await db.execute(
            "INSERT INTO barcodes (barcode, created_timestamp, status) VALUES (?, ?, ?)",
            (barcode, timestamp(), status),
        )


async def read(limit=50, not_uploaded_only=False):
    """
    Read records from the database.

    Args:
        limit: Maximum number of records to return (default: 50)
        not_uploaded_only: If True, only return records where uploaded_timestamp is NULL (default: False)

    Returns:
        Generator yielding record dictionaries
    """
    async with db_readonly() as db:
        query = "SELECT id, barcode, created_timestamp, uploaded_timestamp, status FROM barcodes"

        if not_uploaded_only:
            query += " WHERE uploaded_timestamp IS NULL"

        query += " ORDER BY created_timestamp DESC LIMIT ?"

        cursor = await db.execute(
            query,
            (limit,),
        )

        async for id, barcode, created_timestamp, uploaded_timestamp, status in cursor:
            yield data(
                id=id,
                barcode=barcode,
                created_timestamp=timestamp_to_datetime(created_timestamp),
                uploaded_timestamp=timestamp_to_datetime(uploaded_timestamp),
                status=status,
            )


async def unsent_events_count(seconds=5):
    """
    Check if there are any records without an uploaded_timestamp.

    Args:
        seconds: Number of seconds from now to filter out recently created records (default: 5)

    Returns:
        int: Number of unsent records
    """
    cutoff_time = timestamp(seconds)  # Negative seconds to exclude recent records

    async with db_readonly() as db:
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

    async with db_transaction() as db:
        cursor = await db.execute(
            "DELETE FROM barcodes WHERE created_timestamp < ?", (cutoff_time,)
        )
        return cursor.rowcount


async def mark_as_uploaded(record_ids):
    """
    Mark the specified records as uploaded by setting their uploaded_timestamp and status.

    Args:
        record_ids: List of record IDs to mark as uploaded

    Returns:
        int: Number of records updated
    """
    if not record_ids:
        return 0

    # Create placeholders for the SQL query using itertools.repeat
    placeholders = ",".join(repeat("?", len(record_ids)))

    async with db_transaction() as db:
        cursor = await db.execute(
            f"UPDATE barcodes SET uploaded_timestamp = ?, status = 'UPLOADED' WHERE id IN ({placeholders})",
            (timestamp(), *record_ids),
        )
        return cursor.rowcount


async def get_settings():
    """
    Get all settings.

    Returns:
        dict: Dictionary of all settings (key-value pairs)
    """
    async with db_readonly() as db:
        cursor = await db.execute("SELECT key, value FROM settings ORDER BY key")

        settings = data()
        async for key, value in cursor:
            settings[key] = value

        return settings


async def _set_setting_internal(settings_dict, db_connection, overwrite_settings=True):
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
            INSERT INTO settings (key, value, created_timestamp)
            VALUES {placeholders}
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                created_timestamp = excluded.created_timestamp
            """,
            params,
        )
    else:
        # If overwrite is disabled, ignore conflicts (keep existing settings)
        cursor = await db_connection.execute(
            f"""
            INSERT INTO settings (key, value, created_timestamp)
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

    async with db_transaction() as db:
        return await _set_setting_internal(
            settings_dict=settings_dict, overwrite_settings=True, db_connection=db
        )
