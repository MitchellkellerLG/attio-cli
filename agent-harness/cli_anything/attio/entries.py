"""List Entries command group: manage entries within Attio lists."""
from __future__ import annotations

import json

import click

from .records import build_filter
from .utils.attio_client import AttioClient
from .utils.formatter import format_output, format_pagination_footer


@click.group("entries", help="Manage list entries.")
def entries_group() -> None:
    pass


@entries_group.command("list", help="List/query entries in a list.")
@click.argument("list_id")
@click.option("--limit", default=500, show_default=True, help="Entries per page (max 500).")
@click.option("--all", "all_pages", is_flag=True, help="Stream all pages (no buffer).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.option("--filter", "filter_exprs", multiple=True,
              help="Filter: key=value, '{json}', or @file.json. Repeatable.")
@click.option("--filter-file", type=click.Path(exists=True),
              help="Path to filter JSON file.")
@click.pass_context
def entries_list(
    ctx: click.Context,
    list_id: str,
    limit: int,
    all_pages: bool,
    output_json: bool,
    filter_exprs: tuple[str, ...],
    filter_file: str | None,
) -> None:
    client: AttioClient = ctx.obj["client"]
    filter_body = build_filter(filter_exprs, filter_file)
    count = 0
    for entry in client.list_entries(
        list_id, limit=limit, all_pages=all_pages, filter=filter_body
    ):
        format_output(entry, as_json=output_json, stream=True)
        count += 1
    if not all_pages:
        format_pagination_footer(count, has_more=(count == limit), as_json=output_json)


@entries_group.command("get", help="Get a list entry by ID.")
@click.argument("list_id")
@click.argument("entry_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def entries_get(ctx: click.Context, list_id: str, entry_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.get_entry(list_id=list_id, entry_id=entry_id)
    format_output(result, as_json=output_json)


@entries_group.command("create", help="Create a list entry.")
@click.argument("list_id")
@click.option("--parent-record-id", required=True, help="ID of the parent record.")
@click.option("--values", "values_json", default=None,
              help="Entry values as JSON (optional).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def entries_create(
    ctx: click.Context,
    list_id: str,
    parent_record_id: str,
    values_json: str | None,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    values = None
    if values_json:
        try:
            values = json.loads(values_json)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON in --values: {e}") from e
    result = client.create_entry(list_id=list_id, parent_record_id=parent_record_id, values=values)
    format_output(result, as_json=output_json)


@entries_group.command("update", help="Update a list entry (PATCH by default, PUT with --overwrite).")
@click.argument("list_id")
@click.argument("entry_id")
@click.option("--values", "values_json", required=True, help="Entry values as JSON.")
@click.option("--overwrite", is_flag=True,
              help="Use PUT (replace multiselect values). Default is PATCH (append).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def entries_update(
    ctx: click.Context,
    list_id: str,
    entry_id: str,
    values_json: str,
    overwrite: bool,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --values: {e}") from e
    result = client.update_entry(list_id=list_id, entry_id=entry_id, values=values, overwrite=overwrite)
    format_output(result, as_json=output_json)


@entries_group.command("delete", help="Delete a list entry.")
@click.argument("list_id")
@click.argument("entry_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def entries_delete(
    ctx: click.Context,
    list_id: str,
    entry_id: str,
    yes: bool,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    if not yes:
        click.confirm(f"Delete entry {entry_id} from list {list_id}?", abort=True)
    result = client.delete_entry(list_id=list_id, entry_id=entry_id)
    format_output(result, as_json=output_json)


@entries_group.command("assert", help="Assert (upsert) a list entry by parent record.")
@click.argument("list_id")
@click.option("--parent-record-id", required=True, help="ID of the parent record.")
@click.option("--values", "values_json", default=None,
              help="Entry values as JSON (optional).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def entries_assert(
    ctx: click.Context,
    list_id: str,
    parent_record_id: str,
    values_json: str | None,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    values = None
    if values_json:
        try:
            values = json.loads(values_json)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON in --values: {e}") from e
    # Attio requires parent_object (string) in the assert payload — fetch from list metadata.
    list_data = client.get_list(list_id)
    raw_po = list_data.get("parent_object") or list_data.get("data", {}).get("parent_object")
    # API returns parent_object as a list (e.g. ["people"]); assert endpoint wants a string.
    parent_object: str | None = raw_po[0] if isinstance(raw_po, list) else raw_po
    result = client.assert_entry(
        list_id=list_id,
        parent_record_id=parent_record_id,
        parent_object=parent_object,
        values=values,
    )
    format_output(result, as_json=output_json)
