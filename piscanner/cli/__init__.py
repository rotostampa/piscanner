from importlib import import_module

import click


@click.group()
@click.pass_context
def cli(ctx):
    pass


for module, cmd in (
    ("switch.cli.listener", "listen_for_barcodes"),
    ("switch.cli.noop", "wait"),
):
    cli.add_command(getattr(import_module(module), cmd))


if __name__ == "__main__":
    cli()
