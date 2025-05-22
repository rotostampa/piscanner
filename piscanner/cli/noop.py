import time

import click


@click.command(help="Test wait")
@click.option("--seconds", default="1", type=int, help="Time to wait for")
def wait(seconds):
    time.sleep(seconds)
    click.echo("nothing to do here")
