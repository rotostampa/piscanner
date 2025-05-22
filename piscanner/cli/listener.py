import asyncio, evdev, click

from evdev.ecodes import ecodes

EV_KEY = ecodes['EV_KEY']
KEY_ENTER = ecodes['KEY_ENTER']

async def print_events(device):

    scancodes = dict(codes())
    buffer = ''

    async for event in device.async_read_loop():
        if event.type == EV_KEY:
            key_event = evdev.categorize(event)
            if key_event.keystate == key_event.key_down:
                code = key_event.scancode
                key = scancodes.get(code, "")
                if code == KEY_ENTER:
                    print(f">>> {buffer}")
                    buffer = ""
                else:
                    buffer += key


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
