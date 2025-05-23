import asyncio

HTML = b"""\
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 92

<!DOCTYPE html>
<html>
<head><title>Static Page</title></head>
<body><h1>Hello, this is a static HTML response!</h1></body>
</html>
"""

async def handle_client(reader, writer):
    # Read whatever client sends (you can limit or ignore this)
    await reader.read(1024)  # read up to 1024 bytes (ignore content)

    # Write the static HTTP response
    writer.write(HTML)
    await writer.drain()

    # Close connection
    writer.close()
    await writer.wait_closed()

async def start_server(port=9800):
    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    print("Serving on port {}...".format(port))
    async with server:
        await server.serve_forever()
