from sanic import Sanic, response
import asyncio
from piscanner.utils.storage import read  # async read function imported


async def stream_html(response_writer):
    await response_writer.write(b"""<!DOCTYPE html>
<html><head>
<title>Barcodes</title>
<link rel="stylesheet" href="https://unpkg.com/@picocss/pico@1.*/css/pico.min.css">
</head><body><main class="container">
<h1>Barcodes</h1>
<table><thead><tr>
<th>ID</th><th>Barcode</th><th>Create Timestamp</th><th>Uploaded Timestamp</th>
</tr></thead><tbody>
""")
    rows = await read()
    for row in rows:
        id_, barcode, create_ts, uploaded_ts = row
        uploaded_ts = uploaded_ts if uploaded_ts is not None else "None"
        await response_writer.write(f"""
<tr><td>{id_}</td><td>{barcode}</td><td>{create_ts}</td><td>{uploaded_ts}</td></tr>
""".encode())

    await response_writer.write(b"</tbody></table></main></body></html>")

app = Sanic("BarcodeApp")

@app.get("/")
async def handle(request):
    return response.stream(stream_html, content_type="text/html")

async def start_server(port = 9800):
    await app.run(host="0.0.0.0", port=port)
