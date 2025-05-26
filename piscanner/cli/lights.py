import asyncio
import click

# Define pins
GREEN_PIN = 2
RED_PIN = 4


def setup_gpio():

    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setwarnings(True)

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(GREEN_PIN, GPIO.OUT)
    GPIO.setup(RED_PIN, GPIO.OUT)

    # Ensure both are off
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(RED_PIN, GPIO.LOW)


def cleanup_gpio():
    import RPi.GPIO as GPIO

    GPIO.cleanup()


# The generic async function
async def control_light(pin: int, duration: float, wait: float):
    import RPi.GPIO as GPIO

    print(f"Turning ON light on GPIO{pin}")
    GPIO.output(pin, GPIO.HIGH)
    await asyncio.sleep(duration)

    print(f"Turning OFF light on GPIO{pin}")
    GPIO.output(pin, GPIO.LOW)
    await asyncio.sleep(wait)


@click.command(help="Test wait")
@click.option("--duration", default="1", type=int, help="Time to wait for")
@click.option("--wait", default="1", type=int, help="Time to wait for")
def alert(duration, wait):

    setup_gpio()
    asyncio.run(control_light(duration=duration, wait=wait, pin=RED_PIN))
    cleanup_gpio()


@click.command(help="Test wait")
@click.option("--duration", default="1", type=int, help="Time to wait for")
@click.option("--wait", default="1", type=int, help="Time to wait for")
def success(duration, wait):

    setup_gpio()
    asyncio.run(control_light(duration=duration, wait=wait, pin=GREEN_PIN))
    cleanup_gpio()
