"""Notes command group — manage notes on records."""
from __future__ import annotations

from typing import Any

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output

notes_group = click.Group("notes", help="Manage notes on records.")


@notes_group.command("create", help="Create a note on a record.")
@click.option("--parent-object", required=True, help="Object slug the note belongs to (e.g. people).")
@click.option("--parent-record-id", required=True, help="ID of the parent record.")
@click.option("--title", required=True, help="Note title.")
@click.option("--content", required=True, help="Note body text.")
@click.option("--format", "note_format", default="plaintext", show_default=True,
              help="Content format (plaintext or markdown).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def notes_create(
    ctx: click.Context,
    parent_object: str,
    parent_record_id: str,
    title: str,
    content: str,
    note_format: str,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.create_note(
        parent_object=parent_object,
        parent_record_id=parent_record_id,
        title=title,
        content=content,
        format=note_format,
    )
    format_output(result, as_json=output_json)


@notes_group.command("get", help="Get a note by ID.")
@click.argument("note_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def notes_get(ctx: click.Context, note_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.get_note(note_id)
    format_output(result, as_json=output_json)


@notes_group.command("list", help="List notes, optionally filtered by parent record.")
@click.option("--parent-object", default=None, help="Filter by parent object slug.")
@click.option("--parent-record-id", default=None, help="Filter by parent record ID.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def notes_list(
    ctx: click.Context,
    parent_object: str | None,
    parent_record_id: str | None,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.list_notes(
        parent_object=parent_object,
        parent_record_id=parent_record_id,
    )
    format_output(result, as_json=output_json)


@notes_group.command("update", help="Update a note's title or content.")
@click.argument("note_id")
@click.option("--title", default=None, help="New title.")
@click.option("--content", default=None, help="New content.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def notes_update(
    ctx: click.Context,
    note_id: str,
    title: str | None,
    content: str | None,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.update_note(note_id, title=title, content=content)
    format_output(result, as_json=output_json)


@notes_group.command("delete", help="Delete a note.")
@click.argument("note_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def notes_delete(ctx: click.Context, note_id: str, yes: bool, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    if not yes:
        click.confirm(f"Delete note {note_id}?", abort=True)
    result = client.delete_note(note_id)
    format_output(result, as_json=output_json)
