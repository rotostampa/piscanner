import asyncio, evdev, click

async def print_events(device):
    async for event in device.async_read_loop():
        print(device.path, evdev.categorize(event), sep=': ')


@click.command(help="Listen for barcode scanner")
def listen():

    devices =[evdev.InputDevice(path) for path in evdev.list_devices()]

    assert len(devices) > 0, "No devices found"

    for device in devices:
        asyncio.ensure_future(print_events(device))

    loop = asyncio.get_event_loop()
    loop.run_forever()
