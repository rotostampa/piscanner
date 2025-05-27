import asyncio
import os
import aiohttp
from collections import defaultdict
from piscanner.utils.storage import read, set_status_mapping, set_setting
from piscanner.utils.machine import get_hostname
import ssl
import re
from piscanner.utils.datastructures import data


async def handle_remote_barcodes(barcodes, verbose, sleep_duration=5):
    # API endpoint details
    API_HOST = os.getenv("PISCANNER_SERVER_HOST") or "sprint24.com"
    API_PATH = "/api/storage/piscanner-notify-barcode/"
    API_KEY = os.getenv("PISCANNER_API_KEY")

    hostname = get_hostname()

    print("handle_remote_barcodes", barcodes)

    return {info.barcode: "Ok" for info in barcodes}

    if not API_KEY:
        if verbose:
            print("⚠️ PISCANNER_API_KEY environment variable not set")

    while True:
        # Collect unsent records
        records = {}
        async for record in read(limit=100, not_uploaded_only=True):
            records[record.id] = record.barcode

        # If we have records to send
        if records:
            url = f"https://{API_HOST}{API_PATH}"

            # Build form data
            form_data = [("hostname", hostname)]
            for barcode in records.values():
                form_data.append(("barcode", barcode))

            print(f"📤 Sending {len(records)} barcodes to {url}...")

            if verbose:

                for barcode in records.values():
                    print(f"📤 Sent barcode: {barcode}")

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # Disable cert verification

            # Send the request asynchronously
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        url,
                        data=form_data,
                        headers={
                            "Authorization": f"Bearer {API_KEY}",
                        },
                        ssl=ssl_context,
                    ) as response:
                        if response.status == 200:
                            print(f"✅ Successfully sent {len(records)} barcodes")

                            # Mark records as uploaded in the database
                            updated_count = await set_status_mapping(
                                tuple(records.keys())
                            )

                            if verbose and updated_count != len(records):
                                print(
                                    f"⚠️ Only updated {updated_count} of {len(records)} barcodes"
                                )
                        elif verbose:
                            print(
                                f"⚠️ Error sending barcodes: {response.status} {response.reason}"
                            )
                except aiohttp.client_exceptions.ClientConnectorError as e:
                    if verbose:
                        print(f"⚠️ Error sending barcodes: {e}")

        elif verbose:
            print("📤 No barcodes to send")

        # Wait before next attempt
        await asyncio.sleep(sleep_duration)


async def handle_settings_barcodes(barcodes, **opts):
    print("rewrite_settings", barcodes, opts)
    return {info.barcode: "SettingChanged" for info in barcodes}


async def handle_invalid_barcodes(barcodes, **opts):
    print("invalid_barcodes", barcodes, opts)
    return {info.barcode: "NotOrder" for info in barcodes}


matchers = (
    (
        re.compile("(?P<name>TOKEN|STEP|HOST|PATH|TEST|DELTA)X(?P<value>.*)"),
        handle_settings_barcodes,
    ),
    (re.compile("44X(?P<id>.*)"), handle_remote_barcodes),
)


async def start_sender(sleep_duration=5, **opts):
    print("not implementer")

    while True:
        # Collect unsent records
        records = {}
        async for record in read(limit=100, not_uploaded_only=True):
            records[record.id] = record.barcode

        if records:
            groups = defaultdict(list)

            barcodes = {}

            for r in frozenset(records.values()):

                match = None

                for compiled, func in matchers:
                    if match := compiled.match(r):
                        groups[func].append(data(barcode=r, **match.groupdict()))

                if not match:
                    groups[handle_invalid_barcodes].append(data(barcode=r))

            for func, items in groups.items():
                results = await func(items, **opts)

                for barcode, status in results.items():
                    barcodes[barcode] = status

            final_data = defaultdict(list)

            for id, barcode in records.items():
                status = barcodes[barcode]
                final_data[status].append(id)

            await set_status_mapping(final_data)

        await asyncio.sleep(sleep_duration)


def sender_coroutines(*args, **opts):
    yield start_sender, args, opts
