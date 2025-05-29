import asyncio
import datetime
from itertools import repeat
from piscanner.utils.storage import read, get_settings
from piscanner.utils.machine import get_hostname, get_local_hostname
from functools import partial


def truncate(text, length=40):
    """Truncate text to specified length and add ellipsis if needed."""
    if len(text) > length:
        return text[:length] + "..."
    return text


def format_value(key, value):
    if key == "TOKEN" and value:
        return "".join(repeat("&bull;", 8))
    if key == "URL" and value:
        return f"<a target='_blank' href='{value}'>{truncate(value)}</a>"
    if key == "INSECURE":
        return bool(value) and "&#x2713;" or "&mdash;"
    return value or "&mdash;"


async def handle_client(reader, writer, verbose=False):
    # Read and ignore client request
    await reader.read(1024)

    context = dict(
        hostname=get_hostname(),
        time=datetime.datetime.now().time().strftime("%H:%M:%S"),
        year=datetime.date.today().year,
    )

    # Write response headers
    headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
    )
    writer.write(headers.encode())
    await writer.drain()

    async def write_chunk(data: str):
        writer.write(f"{len(data):X}\r\n".encode())
        writer.write(data.encode())
        writer.write(b"\r\n")
        await writer.drain()

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
  <h1>&#129302; {hostname} <small style='color:gray;font-size:10px;padding-left: 30px'>Last updated &rarr; {time}</small></h1>
  <h2>Barcodes</h2>
  <div class="barcode-grid">
""".format(
            **context
        )
    )

    # Stream barcode rows one by one as cards
    async for row in read():
        # Truncate barcode if longer than 21 characters
        row.truncated_barcode = truncate(row.barcode, 21)
        await write_chunk(
            """
            <article>
              <dl class="card-content">

                <dt>Barcode {id}</dt>
                <dd title="{barcode}">{truncated_barcode}</dd>

                <dt>Status</dt>
                <dd>{status}</dd>

                <dt>Created</dt>
                <dd><small>{created_timestamp}</small></dd>

                <dt>Completed</dt>
                <dd><small>{completed_timestamp}</small></dd>
              </dl>
            </article>
        """.format(
                **row
            )
        )

    # Close barcodes grid
    await write_chunk("</div>")

    # Add spacing between sections
    await write_chunk('<div style="margin: 20px 0;"></div>')

    # Add settings section as a single card
    await write_chunk(
        '''<h2>Settings</h2>
           <div class="barcode-grid">
             <article>
               <dl class="card-content">'''
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

    # Last chunk
    writer.write(b"0\r\n\r\n")
    await writer.drain()

    writer.close()
    await writer.wait_closed()

    if verbose:
        print("🤖 server request completed")


async def start_server(address="0.0.0.0", port=9999, verbose=False):
    server = await asyncio.start_server(
        partial(handle_client, verbose=verbose), address, port
    )
    print("🤖 Serving on http://{}:{}...".format(get_local_hostname(), port))
    async with server:
        await server.serve_forever()


def server_coroutines(*args, **opts):
    yield start_server, args, opts
