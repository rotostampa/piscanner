from importlib import import_module

import click


@click.group()
@click.pass_context
def cli(ctx):
    pass


for module, cmd in (
    ("piscanner.cli.start", "start"),
    ("piscanner.cli.noop", "noop"),
    ("piscanner.cli.populate", "populate"),
    ("piscanner.cli.lights", "lights"),
    ("piscanner.cli.populate", "cleanup"),
):
    cli.add_command(getattr(import_module(module), cmd))


if __name__ == "__main__":
    cli()
