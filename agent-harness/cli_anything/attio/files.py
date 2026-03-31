"""Files command group: upload, download, and manage files on records."""
from __future__ import annotations

import sys
from typing import Any

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


files_group = click.Group("files", help="Upload, download, and manage files on records.")


@files_group.command("upload", help="Upload a file to a record.")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True),
              help="Path to the file to upload.")
@click.option("--record-id", required=True, help="Record ID to attach the file to.")
@click.option("--object", "object_slug", required=True,
              help="Object slug (e.g. people, companies).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def upload_cmd(
    ctx: click.Context,
    file_path: str,
    record_id: str,
    object_slug: str,
    output_json: bool,
) -> None:
    """Upload a binary file to a record via multipart form."""
    client: AttioClient = ctx.obj["client"]
    result = client.upload_file(file_path, record_id, object_slug)
    format_output(result, as_json=output_json)


@files_group.command("get", help="Get file metadata by ID.")
@click.argument("file_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def get_cmd(ctx: click.Context, file_id: str, output_json: bool) -> None:
    """Get metadata for a file by its ID."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_file_info(file_id)
    format_output(result, as_json=output_json)


@files_group.command("list", help="List files, optionally filtered by record.")
@click.option("--record-id", default=None, help="Filter files by record ID.")
@click.option("--object", "object_slug", default=None,
              help="Filter files by object slug (e.g. people).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def list_cmd(
    ctx: click.Context,
    record_id: str | None,
    object_slug: str | None,
    output_json: bool,
) -> None:
    """List files. Use --record-id and/or --object to filter."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_files(record_id=record_id, object_slug=object_slug)
    format_output(result, as_json=output_json)


@files_group.command("download", help="Download a file to disk or stdout.")
@click.argument("file_id")
@click.option("--output", "output_path", default=None,
              help="Output path. If omitted, writes raw bytes to stdout.")
@click.pass_context
def download_cmd(ctx: click.Context, file_id: str, output_path: str | None) -> None:
    """Download a file by ID. Use --output to save to disk; omit for stdout (pipe-friendly)."""
    client: AttioClient = ctx.obj["client"]
    data = client.download_file(file_id)
    if output_path:
        with open(output_path, "wb") as fh:
            fh.write(data)
        click.echo(f"Downloaded {len(data)} bytes to {output_path}")
    else:
        sys.stdout.buffer.write(data)


@files_group.command("delete", help="Delete a file by ID.")
@click.argument("file_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def delete_cmd(ctx: click.Context, file_id: str, yes: bool, output_json: bool) -> None:
    """Delete a file by its ID."""
    client: AttioClient = ctx.obj["client"]
    if not yes:
        click.confirm(f"Delete file {file_id}?", abort=True)
    result = client.delete_file(file_id)
    format_output(result, as_json=output_json)


@files_group.command("create-folder", help="Create a folder on a record.")
@click.option("--name", required=True, help="Folder name.")
@click.option("--record-id", required=True, help="Record ID to attach the folder to.")
@click.option("--object", "object_slug", required=True,
              help="Object slug (e.g. people, companies).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def create_folder_cmd(
    ctx: click.Context,
    name: str,
    record_id: str,
    object_slug: str,
    output_json: bool,
) -> None:
    """Create a folder on a record."""
    client: AttioClient = ctx.obj["client"]
    result = client.create_folder(name, record_id, object_slug)
    format_output(result, as_json=output_json)
