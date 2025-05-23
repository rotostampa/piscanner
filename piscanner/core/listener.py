import evdev
import warnings
import sys

from evdev.ecodes import ecodes
from piscanner.utils.machine import get_machine_uuid
from piscanner.utils.storage import insert_barcode



BARCODE_TERMINATOR = ecodes["KEY_ENTER"]

EV_KEY = ecodes["EV_KEY"]
KEY_LEFTSHIFT = ecodes["KEY_LEFTSHIFT"]
KEY_RIGHTSHIFT = ecodes["KEY_RIGHTSHIFT"]


async def print_events(device):

    scancodes = dict(codes())
    shifted_scancodes = dict(shifted_codes())
    buffer = ""
    shift_pressed = False

    print(f"Listening on {device.name} at {device.path}, VID={device.info.vendor}, PID={device.info.product}, Serial={device.uniq}")


    #print("KEY_ENTER: {} EV_KEY: {}".format(KEY_ENTER, EV_KEY))
    #print("Scancodes", scancodes)
    #print("Shifted scancodes", shifted_scancodes)
    #print("-" * 20)

    async for event in device.async_read_loop():
        if event.type == EV_KEY:
            key_event = evdev.categorize(event)
            code = key_event.scancode

            # Handle shift key state
            if code in [KEY_LEFTSHIFT, KEY_RIGHTSHIFT]:
                shift_pressed = key_event.keystate == key_event.key_down
                #print(f'SHIFT {"PRESSED" if shift_pressed else "RELEASED"}')
                continue

            # Only process key down events for other keys
            if key_event.keystate == key_event.key_down:
                #print("GOT CODE", code, "SHIFT:", shift_pressed)

                if code == BARCODE_TERMINATOR:
                    if buffer:  # Only print if there's content
                        await insert_barcode(buffer.strip())
                    buffer = ""
                else:
                    # Choose character based on shift state
                    if shift_pressed and code in shifted_scancodes:
                        char = shifted_scancodes.get(code, "")
                    else:
                        char = scancodes.get(code, "")

                    if char:
                        buffer += char


def codes():
    # Letters (lowercase)
    for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        yield ecodes["KEY_{}".format(c)], c.lower()

    # Common punctuation that might appear in barcodes
    punctuation_map = {
        "KEY_SPACE": " ",
        "KEY_MINUS": "-",
        "KEY_EQUAL": "=",
        "KEY_LEFTBRACE": "[",
        "KEY_RIGHTBRACE": "]",
        "KEY_SEMICOLON": ";",
        "KEY_APOSTROPHE": "'",
        "KEY_GRAVE": "`",
        "KEY_BACKSLASH": "\\",
        "KEY_COMMA": ",",
        "KEY_DOT": ".",
        "KEY_SLASH": "/",
    }

    for key_name, char in punctuation_map.items():
        if key_name in ecodes:
            yield ecodes[key_name], char


def shifted_codes():
    # Letters (uppercase when shifted)
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        yield ecodes["KEY_{}".format(c)], c.upper()

    # Numbers become symbols when shifted
    number_symbols = {
        "KEY_1": "!",
        "KEY_2": "@",
        "KEY_3": "#",
        "KEY_4": "$",
        "KEY_5": "%",
        "KEY_6": "^",
        "KEY_7": "&",
        "KEY_8": "*",
        "KEY_9": "(",
        "KEY_0": ")",
    }

    for key_name, symbol in number_symbols.items():
        yield ecodes[key_name], symbol

    # Punctuation symbols when shifted
    shifted_punctuation = {
        "KEY_MINUS": "_",
        "KEY_EQUAL": "+",
        "KEY_LEFTBRACE": "{",
        "KEY_RIGHTBRACE": "}",
        "KEY_SEMICOLON": ":",
        "KEY_APOSTROPHE": '"',
        "KEY_GRAVE": "~",
        "KEY_BACKSLASH": "|",
        "KEY_COMMA": "<",
        "KEY_DOT": ">",
        "KEY_SLASH": "?",
    }

    for key_name, char in shifted_punctuation.items():
        if key_name in ecodes:
            yield ecodes[key_name], char



def listener_coroutines():

    print("Starting on machine {}".format(get_machine_uuid()))

    sys.stdout.flush()

    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    if len(devices) == 0:
        warnings.warn("No devices found")

    for device in devices:
        yield print_events, (), {"device": device}
