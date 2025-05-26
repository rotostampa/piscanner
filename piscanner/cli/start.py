from importlib import import_module
import traceback
import asyncio
import click
import signal
import sys
from piscanner.utils.storage import init
import warnings
from piscanner.utils.machine import is_mac
from piscanner.utils.lights import setup_gpio, cleanup_gpio


def yield_coroutines():
    for module, cmd, check in (
        ("piscanner.core.listener", "listener_coroutines", not is_mac),
        ("piscanner.core.server", "server_coroutines", True),
        ("piscanner.core.sender", "sender_coroutines", True),
        ("piscanner.core.lights", "lights_coroutines", True),
    ):
        if check:
            func = getattr(import_module(module), cmd)
            yield from func()
        else:
            warnings.warn("Warning {}.{} won't run on your system".format(module, cmd))


async def restart_on_failure(coroutine_func, *args, **kwargs):
    while True:
        try:
            await coroutine_func(*args, **kwargs)
        except Exception:
            print(f"Coroutine {coroutine_func} failed with exception:")
            traceback.print_exc()  # prints traceback to stderr by default
            await asyncio.sleep(1)


def signal_handler(sig, frame):
    """Handle signals like SIGINT (Ctrl+C) by cleaning up GPIO first"""
    print("Cleaning up GPIO and exiting...")
    cleanup_gpio()
    sys.exit(0)


async def main(**kwargs):

    setup_gpio()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await init()

    for coroutine, args, opts in yield_coroutines():
        asyncio.create_task(restart_on_failure(coroutine, *args, **opts, **kwargs))

    try:
        # Run forever
        await asyncio.Event().wait()
    finally:
        # Ensure cleanup even if the event loop is stopped
        cleanup_gpio()


@click.command(help="Listen for barcode scanner")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def start(verbose):
    asyncio.run(main(verbose = verbose))
