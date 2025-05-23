from importlib import import_module
import traceback
import asyncio
import click
from piscanner.utils.storage import init
import warnings
from piscanner.utils.machine import is_mac


def yield_coroutines():
    for module, cmd, check in (
        ("piscanner.core.listener", "listener_coroutines", not is_mac),
        ("piscanner.core.server", "server_coroutines", True),
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


async def main():
    await init()

    for coroutine, args, opts in yield_coroutines():
        asyncio.create_task(restart_on_failure(coroutine, *args, **opts))

    # Run forever
    await asyncio.Event().wait()


@click.command(help="Listen for barcode scanner")
def start():
    asyncio.run(main())
