import asyncio, evdev, click

from evdev.ecodes import ecodes

async def print_events(device):
    async for event in device.async_read_loop():
        print(device.path, evdev.categorize(event), sep=': ')

def codes():
    for c in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        yield c, ecodes['KEY_{}'.format(c)]

@click.command(help="Listen for barcode scanner")
def listen():

    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    assert len(devices) > 0, "No devices found"

    for device in devices:
        print('Listening on', device.path)
        asyncio.ensure_future(print_events(device))

    loop = asyncio.get_event_loop()
    loop.run_forever()
