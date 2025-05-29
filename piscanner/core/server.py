import asyncio
import datetime
from itertools import repeat
from functools import partial
from piscanner.utils.storage import read, get_settings
from piscanner.utils.machine import get_hostname, get_local_hostname
from aiohttp import web
from urllib.parse import urlparse


def truncate(text, length=40):
    """Truncate text to specified length and add ellipsis if needed."""
    if len(text) > length:
        return text[:length] + "..."
    return text


def format_date(dt):
    """Format datetime object or return long dash if None."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "&mdash;"


def is_success(status):
    """Check if status indicates success (starts with 'Moved')."""
    return status and status.startswith("Moved")


def format_value(key, value):
    if key == "TOKEN" and value:
        return "".join(repeat("&bull;", 8))
    if key == "INSECURE":
        return bool(value) and "&#x2713;" or "&mdash;"
    if key == "URL" and value:
        if netloc := urlparse(value).netloc or value:
            return f"<a target='_blank' href='{value}'>{netloc}</a>"
    return value or "&mdash;"

def is_connection_valid(request, response):
    return request.transport and not request.transport.is_closing()

async def handle_client(request, verbose=False):
    context = dict(
        hostname=get_hostname(),
        time=datetime.datetime.now().time().strftime("%H:%M:%S"),
        year=datetime.date.today().year,
    )

    # Create streaming response
    response = web.StreamResponse()
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.enable_chunked_encoding()
    await response.prepare(request)

    async def write_chunk(data: str):
        if is_connection_valid(request, response):
            try:
                await response.write(data.encode())
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass

    # Write the first chunk: HTML header + styled container with responsive grid
    await write_chunk(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="refresh" content="3">
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{hostname}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" />
    <style>
        /* Hide scrollbars for all browsers */
        html {{
            scrollbar-width: none; /* Firefox */
            -ms-overflow-style: none; /* Internet Explorer 10+ */
        }}
        html::-webkit-scrollbar {{
            display: none; /* WebKit browsers (Chrome, Safari, Edge) */
        }}
        body {{
            overflow-x: hidden;
            overflow-y: auto;
        }}
        .header-title {{
            display: flex;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .last-updated {{
            color: gray;
            font-size: 10px;
        }}
        @media (max-width: 767px) {{
            .header-title {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.25rem;
                margin-bottom: 1.5rem;
            }}
            .last-updated {{
                font-size: 12px;
            }}
        }}
        .barcode-grid {{
            display: grid;
            gap: 1rem;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        }}
        .card-content {{
            display: grid;
            grid-template-columns: minmax(100px, 30%) 1fr;
            gap: 0.5rem;
            margin: 0;
            padding: 0;
        }}
        .card-content dt {{
            font-weight: bold;
            color: var(--muted-color);
            align-self: start;
        }}
        .card-content dd {{
            margin: 0;
            align-self: start;
        }}
        article {{
            margin-bottom: 0;
            position: relative;
        }}
        .success-indicator {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            color: var(--pico-color-green-500, #28a745);
            font-size: 1.2rem;
        }}
        @media (min-width: 768px) {{
            .barcode-grid {{
                grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            }}
        }}
    </style>
</head>
<body class="container">
  <br/>
  <div class="header-title">
    <h1>&#129302; {hostname}</h1>
    <small class="last-updated">Last updated &rarr; {time}</small>
  </div>
  <h2>Barcodes</h2>
  <div class="barcode-grid">
""".format(
            **context
        )
    )

    # Stream barcode rows one by one as cards
    async for row in read(
    ):
        # Truncate barcode if longer than 21 characters
        success_indicator = '<div class="success-indicator">&#x2713;</div>' if is_success(row.get('status')) else ''
        await write_chunk(
            """
            <article>
              {success_indicator}
              <dl class="card-content">

                <dt>Barcode {id}</dt>
                <dd title="{barcode}">{truncated_barcode}</dd>

                <dt>Status</dt>
                <dd>{status}</dd>

                <dt>Processed</dt>
                <dd>{timestamp}</dd>
              </dl>
            </article>
        """.format(
                **row, truncated_barcode=truncate(row.barcode, 21), success_indicator=success_indicator,
                timestamp = format_date(row.completed_timestamp or row.created_timestamp)
            )
        )

    # Close barcodes grid
    await write_chunk("</div>")

    # Add spacing between sections
    await write_chunk('<div style="margin: 20px 0;"></div>')

    # Add settings section as a single card
    await write_chunk(
        """<h2>Settings</h2>
           <div class="barcode-grid">
             <article>
               <dl class="card-content">"""
    )

    # Get and display settings in the single card
    settings = await get_settings()
    for key, value in settings.items():
        await write_chunk(
            """
                <dt>{key}</dt>
                <dd>{value}</dd>
        """.format(
                key=key, value=format_value(key, value)
            )
        )

    # Write closing tags
    await write_chunk(
        "</dl></article></div><footer style='color:gray; text-align:center; margin-top: 2rem;'>Made with &#10084;&#65039; by Rotostampa</footer><br/></body></html>"
    )

    # Close the response
    if is_connection_valid(request, response):
        await response.write_eof()

    if verbose:
        print("🤖 server request completed")

    return response


async def start_server(address="0.0.0.0", port=9999, verbose=False):
    app = web.Application()

    app.router.add_get("/", partial(handle_client, verbose=verbose))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, address, port)
    await site.start()

    print("🤖 Serving on http://{}:{}...".format(get_local_hostname(), port))

    while True:
        await asyncio.sleep(3600)


def server_coroutines(*args, **opts):
    yield start_server, args, opts
