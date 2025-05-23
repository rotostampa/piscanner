from aiohttp import web
import asyncio
from piscanner.utils.storage import read

# Assuming read() is imported or defined in the same module
# from your_module import read


async def handle(request):
    rows = await read()

    # Build HTML rows for the table
    table_rows = ""
    for row in rows:
        # row = (id, barcode, create_timestamp, uploaded_timestamp)
        id_, barcode, create_ts, uploaded_ts = row
        uploaded_ts_str = str(uploaded_ts) if uploaded_ts is not None else "None"
        table_rows += f"""
        <tr>
            <td>{id_}</td>
            <td>{barcode}</td>
            <td>{create_ts}</td>
            <td>{uploaded_ts_str}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
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
                    {table_rows}
                </tbody>
            </table>
        </main>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")


async def start_app(port = 80):
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
