import asyncio
import os
import aiohttp
from piscanner.utils.storage import read, mark_as_uploaded
from piscanner.utils import json


async def start_sender(verbose, sleep_duration=5):
    # API endpoint details
    API_HOST = os.getenv("PISCANNER_SERVER_HOST") or "sprint24.com"
    API_PATH = "/api/storage/piscanner-notify-barcode/"
    API_KEY = os.getenv("PISCANNER_API_KEY")

    if not API_KEY:
        if verbose:
            print("⚠️ PISCANNER_API_KEY environment variable not set")

    while True:
        # Collect unsent records
        records = []
        async for record in read(limit=100, not_uploaded_only=True):
            # Add records without manual datetime conversion
            records.append(record)

        # If we have records to send
        if records:
            if verbose:
                print(f"📤 Sending {len(records)} records to server...")

            # Send the request asynchronously
            async with aiohttp.ClientSession(json_serialize=json.dumps) as session:
                async with session.post(
                    f"https://{API_HOST}{API_PATH}",
                    json=records,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {API_KEY}",
                    },
                ) as response:
                    if response.status == 200:
                        print(f"✅ Successfully sent {len(records)} records")
                        if verbose:
                            for record in records:
                                print("📤 Sent record: {id}".format(**record))

                        # Mark records as uploaded in the database
                        updated_count = await mark_as_uploaded(
                            tuple(record["id"] for record in records)
                        )

                        if verbose and updated_count != len(records):
                            print(
                                f"⚠️ Only updated {updated_count} of {len(records)} records"
                            )
                    elif verbose:
                        # response_text = await response.text()

                        print(
                            f"⚠️ Error sending records: {response.status} {response.reason}"
                        )
                        # print(f"Response: {response_text}")
        elif verbose:
            print("📤 No records to send")

        # Wait before next attempt
        await asyncio.sleep(sleep_duration)


def sender_coroutines(*args, **opts):
    yield start_sender, args, opts
