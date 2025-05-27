import asyncio
import datetime
from piscanner.utils.storage import read
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
    <thead>
      <tr>
        <th>ID</th><th>Barcode</th><th>Create Timestamp</th><th>Uploaded Timestamp</th>
      </tr>
    </thead>
    <tbody>
""".format(
            **context
        )
    )

    # Stream rows one by one
    async for row in read():
        await write_chunk(
            """
            <tr>
            <td>{id}</td>
            <td>{barcode}</td>
            <td>{created_timestamp}</td>
            <td>{uploaded_timestamp}</td>
            </tr>
        """.format(
                **row
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
