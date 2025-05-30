from importlib import import_module
import traceback
import asyncio
import click
import signal
import sys
from piscanner.utils.storage import init
from piscanner.utils.machine import is_mac
from piscanner.utils.lights import setup_gpio, cleanup_gpio


SERVICES = {
    "listener": ("piscanner.core.listener", "listener_coroutines"),
    "server": ("piscanner.core.server", "server_coroutines"),
    "worker": ("piscanner.core.worker", "worker_coroutines"),
}


def yield_coroutines(services):
    for service in services:
        module_name, cmd = SERVICES[service]

        func = getattr(import_module(module_name), cmd)

        yield from func()


async def restart_on_failure(coroutine_func, *args, **kwargs):
    while True:
        try:
            await coroutine_func(*args, **kwargs)
        except Exception:
            print(f"Coroutine {coroutine_func} failed with exception:")
            traceback.print_exc()  # prints traceback to stderr by default
            await asyncio.sleep(1)




async def main(services, **kwargs):



    await init()

    for coroutine, args, opts in yield_coroutines(services):
        asyncio.create_task(restart_on_failure(coroutine, *args, **opts, **kwargs))

    await asyncio.Event().wait()


@click.command(help="Start PiScanner services")
@click.argument("services", nargs=-1, type=click.Choice(tuple(SERVICES.keys())))
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def start(services, **opts):
    # If no services specified, start all available services
    if not services:

        services = set(SERVICES.keys())

        if is_mac:
            # On Mac, exclude listener by default
            services.remove("listener")

    asyncio.run(main(services, **opts))
