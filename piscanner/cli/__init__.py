from importlib import import_module

import click, sys

@click.group()
@click.pass_context
def cli(ctx):
    pass


for module, cmd in (
    ("piscanner.cli.listener", "listen"),
    ("piscanner.cli.noop", "wait"),
):
    cli.add_command(getattr(import_module(module), cmd))


if __name__ == "__main__":
    cli()
