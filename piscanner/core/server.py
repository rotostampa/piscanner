from aiohttp import web
import asyncio
from piscanner.utils.storage import read

# Assuming read() is imported or defined in the same module
# from your_module import read


# HTML handler with streaming
async def handle(request):
    response = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'text/html'})
    await response.prepare(request)

    await response.write(b"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Barcodes</title>
    <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@1.*/css/pico.min.css" />
</head>
<body>
<main class="container">
    <h1>Barcodes</h1>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Barcode</th>
                <th>Create Timestamp</th>
                <th>Uploaded Timestamp</th>
            </tr>
        </thead>
        <tbody>
""")

    rows = await read()
    for row in rows:
        id_, barcode, create_ts, uploaded_ts = row
        uploaded_ts_str = str(uploaded_ts) if uploaded_ts is not None else "None"
        row_html = f"""
            <tr>
                <td>{id_}</td>
                <td>{barcode}</td>
                <td>{create_ts}</td>
                <td>{uploaded_ts_str}</td>
            </tr>
        """
        await response.write(row_html.encode())

    await response.write(b"""
        </tbody>
    </table>
</main>
</body>
</html>
""")
    await response.write_eof()
    return response


async def start_server(port = 9800):
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    print(f"Serving on http://0.0.0.0:{port}")
    await site.start()

    # Run forever
    while True:
        await asyncio.sleep(3600)
