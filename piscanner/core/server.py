import asyncio
import datetime
import logging
import os
import sys
from itertools import repeat
from urllib.parse import urlparse

from aiohttp import web

import piscanner
from piscanner.utils.machine import get_hostname, get_local_hostname
from piscanner.utils.storage import get_settings, read


def format_date(dt):
    """Format datetime object or return long dash if None."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "&mdash;"


def is_success(status):
    """Check if status indicates success (starts with 'Moved')."""
    return status.startswith("Moved") or status in ("SettingsChanged", "Scanned")


def is_recent(created_timestamp, seconds=10):
    """Check if barcode was created within the last N seconds."""
    now = datetime.datetime.now(created_timestamp.tzinfo)
    return (now - created_timestamp).total_seconds() <= seconds


def format_value(key, value):
    if key == "TOKEN" and value:
        return "".join(repeat("&bull;", 8))
    if key == "INSECURE":
        return bool(value) and "&#x2713;" or "&mdash;"
    if key == "URL" and value and (netloc := urlparse(value).netloc or value):
        return f"<a target='_blank' href='{value}'>{netloc}</a>"
    return value or "&mdash;"


# Add JSON refresh endpoint
async def refresh_data(request):

    # Collect settings data
    settings = await get_settings()
    settings_data = {key: format_value(key, value) for key, value in settings.items()}

    # Collect barcodes data
    barcodes_data = []
    async for row in read():
        barcode_entry = {
            "id": row.id,
            "barcode": row.barcode,
            "status": row.status,
            "created_timestamp": format_date(row.created_timestamp),
            "completed_timestamp": format_date(row.completed_timestamp),
            "is_success": is_success(row.status),
            "is_recent": (
                is_recent(row.created_timestamp) if row.created_timestamp else False
            ),
        }
        barcodes_data.append(barcode_entry)

    return web.json_response(
        {
            "hostname": get_hostname(),
            "settings": settings_data,
            "barcodes": barcodes_data,
        }
    )


async def start_server(address="0.0.0.0", port=9999, verbose=False):

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
    )

    # Enable access logging
    logging.getLogger("aiohttp.access").setLevel(logging.INFO)

    app = web.Application()

    static_path = os.path.abspath(
        os.path.join(os.path.dirname(piscanner.__file__), "static")
    )

    logs_path = os.path.expanduser("~/logs")

    # Serve Preact app for main route
    async def serve_main_app(request):
        return web.FileResponse(os.path.join(static_path, "index.html"))

    app.router.add_get("/", serve_main_app)
    app.router.add_get("/refresh/", refresh_data)

    if os.path.exists(logs_path):
        app.router.add_static('/logs/', logs_path, name='logs', show_index=True)

    # Add static file serving for /static/ route
    # app.router.add_static('/static/', static_path, name='static')

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, address, port)
    await site.start()

    print(f"🤖 Serving on http://{get_local_hostname()}:{port}...")

    while True:
        await asyncio.sleep(3600)


def server_coroutines(*args, **opts):
    yield start_server, args, opts
