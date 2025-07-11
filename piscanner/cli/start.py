import asyncio
import contextlib
import traceback
from importlib import import_module

import click

from piscanner.utils.machine import is_mac
from piscanner.utils.storage import init

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

    for func, args, opts in yield_coroutines(services):
        asyncio.create_task(restart_on_failure(func, *args, **opts, **kwargs))

    await asyncio.Event().wait()


@click.command(help="Start PiScanner services")
@click.argument("services", nargs=-1, type=click.Choice(tuple(SERVICES.keys())))
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def start(services, **opts):

    services = set(services or SERVICES.keys())

    if is_mac:
        with contextlib.suppress(KeyError):
            services.remove("listener")

    asyncio.run(main(services, **opts))
