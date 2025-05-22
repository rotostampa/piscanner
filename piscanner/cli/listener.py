import click



import evdev
from evdev import InputDevice, categorize, ecodes

def find_barcode_device():
    devices = [InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        name = device.name.lower()
        print('found', name, device)
        if 'barcode' in name or 'scanner' in name:
            print(f"Found barcode reader: {device.name} at {device.path}")
            return device
    raise Exception("Barcode reader not found")

def read_barcode(device):
    scancodes = {
        2: '1', 3: '2', 4: '3', 5: '4',
        6: '5', 7: '6', 8: '7', 9: '8',
        10: '9', 11: '0',
        28: 'ENTER',
        30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g',
        35: 'h', 36: 'j', 37: 'k', 38: 'l',
        44: 'z', 45: 'x', 46: 'c', 47: 'v',
        48: 'b', 49: 'n', 50: 'm',
    }

    buffer = ""

    print(f"Listening for input on {device.path} ({device.name})")
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            if key_event.keystate == key_event.key_down:
                code = key_event.scancode
                key = scancodes.get(code, '')
                if key == 'ENTER':
                    print(f">>> {buffer}")
                    buffer = ""
                else:
                    buffer += key



@click.command(help="Listen for barcode scanner")
def listen():
    print('to be implemented')
    try:
        device = find_barcode_device()
        read_barcode(device)
    except Exception as e:
        print("Error:", e)
