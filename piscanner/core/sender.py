import asyncio

import json
import os
import aiohttp
from piscanner.utils.storage import read, mark_as_uploaded


async def start_sender(verbose, sleep_duration=5):
    # API endpoint details
    API_HOST = "sprint24.com"
    API_PATH = "/api/storage/piscanner-notify-barcode/"
    API_KEY = os.getenv("PISCANNER_API_KEY")

    if not API_KEY:
        if verbose:
            print("⚠️ PISCANNER_API_KEY environment variable not set")

    while True:
        # Collect unsent records
        records = []
        async for record in read(limit=100, not_uploaded_only=True):
            # Convert datetime objects to ISO format strings for JSON serialization
            records.append({
                "id": record["id"],
                "barcode": record["barcode"],
                "created_timestamp": (
                    record["created_timestamp"].isoformat()
                    if record["created_timestamp"]
                    else None
                ),
            })

        # If we have records to send
        if records:
            if verbose:
                print(f"📤 Sending {len(records)} records to server...")

            # Send the request asynchronously
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://{API_HOST}{API_PATH}",
                    json={"records": records},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {API_KEY}",
                    }
                ) as response:
                    if response.status == 200:
                        if verbose:
                            print(f"✅ Successfully sent {len(records)} records")

                        # Mark records as uploaded in the database
                        updated_count = await mark_as_uploaded(tuple(record["id"] for record in records))

                        if verbose and updated_count != len(records):
                            print(
                                f"⚠️ Only updated {updated_count} of {len(records)} records"
                            )
                    else:
                        response_text = await response.text()
                        if verbose:
                            print(
                                f"❌ Error sending records: {response.status} {response.reason}"
                            )
                            print(f"Response: {response_text}")
        else:
            if verbose:
                print("📤 No records to send")

        # Wait before next attempt
        await asyncio.sleep(sleep_duration)


def sender_coroutines(*args, **opts):
    yield start_sender, args, opts
