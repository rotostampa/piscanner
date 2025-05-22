import click
import evdev
from evdev import InputDevice, categorize, ecodes
import itertools
import select

def find_barcode_devices():
    devices = [InputDevice(path) for path in evdev.list_devices()]
    if not devices:
        raise RuntimeError("No barcode input devices found")
    for device in devices:
        print(f"Found barcode reader: {device.name} at {device.path}")
    return devices

def read_barcodes(devices):
    scancodes = {
        2: "1", 3: "2", 4: "3", 5: "4", 6: "5",
        7: "6", 8: "7", 9: "8", 10: "9", 11: "0",
        28: "ENTER",
        30: "a", 31: "s", 32: "d", 33: "f", 34: "g",
        35: "h", 36: "j", 37: "k", 38: "l",
        44: "z", 45: "x", 46: "c", 47: "v",
        48: "b", 49: "n", 50: "m",
    }

    buffers = {dev.fd: "" for dev in devices}

    print("Listening for input on devices:")
    for dev in devices:
        print(f"- {dev.path} ({dev.name})")

    try:
        while True:
            r, _, _ = select.select(devices, [], [])
            for dev in r:
                for event in dev.read():
                    if event.type == ecodes.EV_KEY:
                        key_event = categorize(event)
                        if key_event.keystate == key_event.key_down:
                            code = key_event.scancode
                            key = scancodes.get(code, "")
                            if key == "ENTER":
                                print(f">>> {buffers[dev.fd]}")
                                buffers[dev.fd] = ""
                            else:
                                buffers[dev.fd] += key
    except KeyboardInterrupt:
        print("\nExiting on user interrupt")

@click.command(help="Listen for barcode scanner")
def listen():
    read_barcodes(find_barcode_devices())
