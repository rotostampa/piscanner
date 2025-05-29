import asyncio
import datetime
from itertools import repeat
from piscanner.utils.storage import read, get_settings
from piscanner.utils.machine import get_hostname, get_local_hostname
from aiohttp import web
from urllib.parse import urlparse
import os
import piscanner


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
    if key == "URL" and value:
        if netloc := urlparse(value).netloc or value:
            return f"<a target='_blank' href='{value}'>{netloc}</a>"
    return value or "&mdash;"





async def start_server(address="0.0.0.0", port=9999, verbose=False):
    app = web.Application()

    static_path = os.path.abspath(os.path.join(os.path.dirname(piscanner.__file__), '..', 'static'))

    # Serve Preact app for main route
    async def serve_main_app(request):
        return web.FileResponse(os.path.join(static_path, 'index.html'))

    app.router.add_get("/", serve_main_app)
    app.router.add_get('/static/', serve_main_app)

    # Add JSON refresh endpoint
    async def refresh_data(request):
        # Collect hostname data
        hostname_data = {
            'hostname': get_hostname(),
            'time': datetime.datetime.now().time().strftime("%H:%M:%S"),
            'year': datetime.date.today().year
        }
        
        # Collect settings data
        settings = await get_settings()
        settings_data = {key: format_value(key, value) for key, value in settings.items()}
        
        # Collect barcodes data
        barcodes_data = []
        async for row in read():
            barcode_entry = {
                'id': row.id,
                'barcode': row.barcode,
                'status': row.status,
                'created_timestamp': format_date(row.created_timestamp),
                'completed_timestamp': format_date(row.completed_timestamp),
                'is_success': is_success(row.status),
                'is_recent': is_recent(row.created_timestamp) if row.created_timestamp else False
            }
            barcodes_data.append(barcode_entry)

        return web.json_response({
            'hostname': hostname_data,
            'settings': settings_data,
            'barcodes': barcodes_data
        })

    app.router.add_get('/refresh/', refresh_data)

    # Add static file serving for /static/ route
    app.router.add_static('/static/', static_path, name='static')

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, address, port)
    await site.start()

    print("🤖 Serving on http://{}:{}...".format(get_local_hostname(), port))

    while True:
        await asyncio.sleep(3600)


def server_coroutines(*args, **opts):
    yield start_server, args, opts
