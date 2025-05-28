import asyncio
import aiohttp
from collections import defaultdict
from piscanner.utils.storage import read, set_status_mapping, set_setting, get_settings
from piscanner.utils.machine import get_hostname
import ssl
import re
from piscanner.utils.datastructures import data
from urllib.parse import urlparse, parse_qs


async def handle_remote_barcodes(barcodes, verbose):
    # API endpoint details
    settings = await get_settings()

    hostname = get_hostname()

    url = "{URL}".format(**settings)

    # Build form data
    form_data = [(settings.HOSTNAME_VAR or "hostname", hostname)]
    for info in barcodes:
        form_data.append((settings.BARCODE_VAR or "barcode", info.barcode))

    print(f"📤 Sending {len(barcodes)} barcodes to {url}...")

    if verbose:

        for info in barcodes:
            print(f"📤 Sent barcode: {info.barcode}")

    ssl_context = ssl.create_default_context()

    if settings.INSECURE:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # Disable cert verification

    # Send the request asynchronously
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                data=form_data,
                headers={
                    "Authorization": "Bearer {TOKEN}".format(**settings),
                },
                ssl=ssl_context,
            ) as response:
                if response.status == 200:
                    print(f"✅ Successfully sent {len(barcodes)} barcodes")

                    return {info.barcode: "Accepted" for info in barcodes}

                if verbose:
                    print(
                        f"⚠️ Error sending barcodes: {response.status} {response.reason}"
                    )

                return {
                    info.barcode: "HTTPError{}".format(response.status)
                    for info in barcodes
                }
        except (
            aiohttp.client_exceptions.ClientConnectorError,
            aiohttp.client_exceptions.InvalidUrlClientError,
        ) as e:
            if verbose:
                print(f"⚠️ Error sending barcodes: {e}")

            return {info.barcode: e.__class__.__name__ for info in barcodes}


async def handle_settings_barcodes(barcodes, verbose=False, **opts):

    result = {}

    settings = {}

    for info in barcodes:

        if verbose:
            print(f"⏳ Processing barcode: {info.barcode}")

        parsed = urlparse(info.barcode)

        if (
            not parsed.scheme == "piscanner"
            and not parsed.path == ""
            and not parsed.netloc == "settings"
        ):
            result[info.barcode] = "InvalidBarcode"

        else:

            result[info.barcode] = "SettingsChanged"

            for k, values in parse_qs(parsed.query, keep_blank_values=True).items():
                for v in values:
                    settings[k] = v

    if verbose:
        print(f"🧑‍🔬 Settings: {settings}")

    if settings:
        await set_setting(settings)

    return result


async def handle_invalid_barcodes(barcodes, **opts):
    print("invalid_barcodes", barcodes, opts)
    return {info.barcode: "InvalidBarcode" for info in barcodes}


matchers = (
    (
        re.compile(r"piscanner://.*"),
        handle_settings_barcodes,
    ),
    (re.compile("[0-9]+X.*"), handle_remote_barcodes),
)


async def start_sender(sleep_duration=5, verbose=False, **opts):

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
                        if verbose:
                            print(
                                f"🧑🏼‍🔬 Matched barcode {r} with function {func.__name__}"
                            )
                        groups[func].append(data(barcode=r, **match.groupdict()))
                        break

                if not match:
                    if verbose:
                        print(f"🧑🏼‍🔬 Invalid barcode {r}")
                    groups[handle_invalid_barcodes].append(data(barcode=r))

            for func, items in groups.items():
                results = await func(items, verbose=verbose, **opts)

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
