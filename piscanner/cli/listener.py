import asyncio, evdev, click

async def print_events(device):
    async for event in device.async_read_loop():
        print(device.path, evdev.categorize(event), sep=': ')


@click.command(help="Listen for barcode scanner")
def listen():

    for device in [evdev.InputDevice(path) for path in evdev.list_devices()]:
        asyncio.ensure_future(print_events(device))

    loop = asyncio.get_event_loop()
    loop.run_forever()
