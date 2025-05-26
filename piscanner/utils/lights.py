import asyncio
from functools import partial

from piscanner.utils.machine import is_mac

lights_lock = asyncio.Lock()

# Define pins
RED_PIN = 2
GREEN_PIN = 3


def setup_gpio():

    if is_mac:
        return

    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)

    # Set up pins with initial LOW state to prevent brief HIGH during setup
    GPIO.setup(GREEN_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(RED_PIN, GPIO.OUT, initial=GPIO.HIGH)


def cleanup_gpio():

    if is_mac:
        return

    import RPi.GPIO as GPIO

    GPIO.cleanup()


# The generic async function
async def control_light(pin: int, duration: float = 1.0, wait: float = 1.0):

    if not is_mac:
        import RPi.GPIO as GPIO

    async with lights_lock:

        print(f"Turning ON light on GPIO{pin}")
        if not is_mac:
            GPIO.output(pin, GPIO.LOW)
        await asyncio.sleep(duration)

        print(f"Turning OFF light on GPIO{pin}")
        if not is_mac:
            GPIO.output(pin, GPIO.HIGH)
        await asyncio.sleep(wait)


flash_green = partial(control_light, pin=GREEN_PIN)
flash_red = partial(control_light, pin=RED_PIN)
