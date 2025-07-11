import asyncio
from functools import partial

from piscanner.utils.machine import is_mac

# Define pins
RED_PIN = 2
YELLOW_PIN = 3
GREEN_PIN = 4

def setup_gpio():

    if is_mac:
        return

    from RPi import GPIO

    GPIO.setmode(GPIO.BCM)

    # Set up pins with initial LOW state to prevent brief HIGH during setup
    #
    for pin in (RED_PIN, GREEN_PIN, YELLOW_PIN):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)


def cleanup_gpio():

    if is_mac:
        return

    from RPi import GPIO

    GPIO.cleanup()


# The generic async function
async def control_light(
    lock,
    pin: int,
    duration: float = 0.3,
    wait: float = 0.2,
    title="Unknown",
    verbose=False,
):

    if not is_mac:
        from RPi import GPIO

    async with lock:

        if verbose:
            print(f"💡 Turning ON light {title} on GPIO{pin}")
        if not is_mac:
            GPIO.output(pin, GPIO.HIGH)
        await asyncio.sleep(duration)

        if verbose:
            print(f"💡 Turning OFF light {title} on GPIO{pin}")
        if not is_mac:
            GPIO.output(pin, GPIO.LOW)
        await asyncio.sleep(wait)


flash_green = partial(control_light, pin=GREEN_PIN, lock=asyncio.Lock(), title="Green")
flash_red = partial(control_light, pin=RED_PIN, lock=asyncio.Lock(), title="Red")
flash_yellow = partial(
    control_light, pin=YELLOW_PIN, lock=asyncio.Lock(), title="Yellow"
)
