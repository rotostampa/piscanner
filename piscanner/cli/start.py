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


def yield_coroutines(server, listener, sender, lights, cleanup):
    for module, cmd, check in (
        ("piscanner.core.listener", "listener_coroutines", listener and not is_mac),
        ("piscanner.core.server", "server_coroutines", server),
        ("piscanner.core.sender", "sender_coroutines", sender),
        ("piscanner.core.lights", "lights_coroutines", lights),
        ("piscanner.core.cleanup", "cleanup_coroutines", cleanup),
    ):
        if check:
            func = getattr(import_module(module), cmd)
            yield from func()
        else:
            print("⚠️ Warning {}.{} won't run on your system".format(module, cmd), file=sys.stderr)


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


async def main(server, listener, sender, lights, cleanup, **kwargs):

    setup_gpio()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await init()

    for coroutine, args, opts in yield_coroutines(
        server, listener, sender, lights, cleanup
    ):
        asyncio.create_task(restart_on_failure(coroutine, *args, **opts, **kwargs))

    try:
        # Run forever
        await asyncio.Event().wait()
    finally:
        # Ensure cleanup even if the event loop is stopped
        cleanup_gpio()


@click.command(help="Listen for barcode scanner")
@click.option("--listener/--no-listener", default=True, help="Enable/disable listener")
@click.option("--server/--no-server", default=True, help="Enable/disable server")
@click.option("--sender/--no-sender", default=True, help="Enable/disable sender")
@click.option("--lights/--no-lights", default=True, help="Enable/disable lights")
@click.option("--cleanup/--no-cleanup", default=True, help="Enable/disable cleanup")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def start(**opts):
    asyncio.run(main(**opts))
