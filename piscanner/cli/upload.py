import http.client
import urllib.parse

import click
from switch.utils.binaries import AWSCLI
from switch.utils.files import expand_files
from switch.utils.run import grab_and_run


@click.command(
    help="Upload files to s3 and signal sprint24 they are ready for collection"
)
@click.argument("files", nargs=-1, type=click.Path())
@click.option("--unique", is_flag=True, help="Add a unique prefix to the files")
@click.option("--notify", is_flag=True, help="Send a notification")
@click.option("--copy", is_flag=True, help="Copy the file instead of moving it")
@click.option(
    "--s3", default="s3://workflow-upload/", help="Add a unique prefix to the files"
)
def upload(files, unique, s3, notify, copy):

    processes = tuple(
        grab_and_run(
            file,
            lambda path, temp, task_id, s3=s3: (AWSCLI, "s3", "cp", path, s3),
            task_name="switch_file_upload",
            unique=unique,
            copy=copy,
            cleanup=True,
        )
        for file in expand_files(*files)
    )

    if notify and processes:

        # Send the POST request

        click.echo("Sending notification", err=True)

        conn = http.client.HTTPSConnection("sprint24.com")

        conn.request(
            "POST",
            "/api/storage/switch-notify-file/",
            body=urllib.parse.urlencode(
                {"token": "5f5d24c0-a0c0-4f6c-b2b4-2414fac5eaa5"}
            ).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        resp = conn.getresponse()

        click.echo(resp.read(), err=True)

        assert resp.status == 200
