import asyncio
from piscanner.utils.storage import read  # async read function imported


async def handle_client(reader, writer):
    # Read and ignore client request
    await reader.read(1024)

    # Write response headers
    headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Transfer-Encoding: chunked\r\n"  # use chunked for streaming
        "\r\n"
    )
    writer.write(headers.encode())
    await writer.drain()

    async def write_chunk(data: bytes):
        # Write chunk size in hex + CRLF
        writer.write(f"{len(data):X}\r\n".encode())
        writer.write(data)
        writer.write(b"\r\n")
        await writer.drain()

    # Write the first chunk: HTML header + table header
    await write_chunk(
        b"""<!DOCTYPE html>
<html>
<head>
    <title>Barcodes</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"></head><body>
<h1>Barcodes</h1>
<table border="1"><thead><tr><th>ID</th><th>Barcode</th><th>Create Timestamp</th><th>Uploaded Timestamp</th></tr></thead><tbody>
"""
    )

    # Stream rows one by one
    rows = await read()
    for row in rows:
        row_html = (
            "<tr>"
            + "".join(f"<td>{col if col is not None else 'None'}</td>" for col in row)
            + "</tr>\n"
        )
        await write_chunk(row_html.encode())

    # Write closing tags
    await write_chunk(b"</tbody></table></body></html>")

    # Write last chunk (zero length) to indicate end of chunks
    writer.write(b"0\r\n\r\n")
    await writer.drain()

    writer.close()
    await writer.wait_closed()


async def start_server(port):
    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    print("Serving on port {}...".format(port))
    async with server:
        await server.serve_forever()


def server_coroutines(port=9800):
    yield start_server, (), {"port": port}
