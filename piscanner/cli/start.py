from importlib import import_module
import traceback
import asyncio
import click


def yield_coroutines():
    for module, cmd in (("piscanner.core.listener", "listener_coroutines"),):
        func = getattr(import_module(module), cmd)

        yield from func()


async def restart_on_failure(coroutine_func, *args, **kwargs):
    while True:
        try:
            await coroutine_func(*args, **kwargs)
        except Exception:
            print(f"Coroutine {coroutine_func} failed with exception:")
            traceback.print_exc()  # prints traceback to stderr by default
            await asyncio.sleep(1)


@click.command(help="Listen for barcode scanner")
def start():

    for coroutine, args, opts in yield_coroutines():
        asyncio.ensure_future(restart_on_failure(coroutine, *args, **opts))

    loop = asyncio.get_event_loop()
    loop.run_forever()
