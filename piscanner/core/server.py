import asyncio
import datetime
from piscanner.utils.storage import read, get_settings
from piscanner.utils.machine import get_hostname
from functools import partial


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

    # Write the first chunk: HTML header + styled table header inside a centered container
    await write_chunk(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="refresh" content="3">
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{hostname}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" />
</head>
<body class="container flow">
  <br/>
  <h1>&#129302; {hostname} <small style='color:gray;font-size:10px;padding-left: 30px'>Last updated &rarr; {time}</small></h1>
  <table>
    <caption style="font-weight: bold; font-size: 1.2em; margin-bottom: 10px; text-align: left;">Barcodes</caption>
    <thead>
      <tr>
        <th>ID</th><th>Barcode</th><th>Status</th><th>Created</th><th>Completed</th>
      </tr>
    </thead>
    <tbody>
""".format(
            **context
        )
    )

    # Stream barcode rows one by one
    async for row in read():
        # Truncate barcode if longer than 20 characters
        row.truncated_barcode = (
            row.barcode[:21] + "..." if len(row.barcode) > 21 else row.barcode
        )
        await write_chunk(
            """
            <tr>
            <td>{id}</td>
            <td title="{barcode}">{truncated_barcode}</td>
            <td>{status}</td>
            <td><small>{created_timestamp}</small></td>
            <td><small>{completed_timestamp}</small></td>
            </tr>
        """.format(
                **row
            )
        )

    # Close barcodes table
    await write_chunk("</tbody></table>")

    # Add spacing between tables
    await write_chunk('<div style="margin: 20px 0;"></div>')

    # Add settings table
    await write_chunk(
        '<table><caption style="font-weight: bold; font-size: 1.2em; margin-bottom: 10px; text-align: left;">Settings</caption><thead><tr><th>Key</th><th>Value</th></tr></thead><tbody>'
    )

    # Get and display settings
    settings = await get_settings()
    for key, value in settings.items():
        await write_chunk(
            """
            <tr>
            <td>{key}</td>
            <td>{value}</td>
            </tr>
        """.format(
                key=key, value=value
            )
        )

    # Write closing tags
    await write_chunk(
        "</tbody></table><footer style='color:gray'>Made with &#10084;&#65039; by Rotostampa</footer><br/></body></html>"
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
    print("🤖 Serving on http://{}:{}...".format(get_hostname(), port))
    async with server:
        await server.serve_forever()


def server_coroutines(*args, **opts):
    yield start_server, args, opts
