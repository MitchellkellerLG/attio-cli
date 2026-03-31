"""Records command groups: people, companies, deals, users, workspaces, records (generic)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output, format_pagination_footer


# ── Filter builder (D-05, D-06) ───────────────────────────────────────────

def _parse_filter_expr(expr: str) -> dict[str, Any]:
    """Parse a single --filter expression. Returns partial filter dict."""
    # @path.json shorthand
    if expr.startswith("@"):
        return json.loads(Path(expr[1:]).read_text())
    # Raw inline JSON
    if expr.strip().startswith("{"):
        try:
            return json.loads(expr)
        except json.JSONDecodeError as e:
            shell = "powershell" if sys.platform == "win32" else "bash"
            hint = (
                f"JSON parse failed: {e}\n"
                f"Tip ({shell}): wrap in single quotes: --filter '{{\"key\": \"value\"}}'"
            )
            raise click.ClickException(hint) from e
    # key=value shorthand
    if "=" in expr:
        key, _, value = expr.partition("=")
        return {key.strip(): {"$eq": value.strip()}}
    raise click.ClickException(
        f"Cannot parse filter: {expr!r}\n"
        "Expected: key=value, '{\"key\": ...}', or @path.json"
    )


def build_filter(
    filter_exprs: tuple[str, ...],
    filter_file: str | None,
) -> dict[str, Any] | None:
    """D-05: Build Attio filter body. filter-file takes precedence."""
    if filter_file:
        path = filter_file.lstrip("@")
        return json.loads(Path(path).read_text())
    if not filter_exprs:
        return None
    merged: dict[str, Any] = {}
    for expr in filter_exprs:
        merged.update(_parse_filter_expr(expr))
    return merged if merged else None


# ── Shared command factory ─────────────────────────────────────────────────

def _make_record_group(object_slug: str, name: str, help_text: str) -> click.Group:
    """Create a fully-featured record command group for a given object slug."""

    @click.group(name=name, help=help_text)
    def group() -> None:
        pass

    @group.command("list", help=f"List/query {name} records.")
    @click.option("--limit", default=500, show_default=True, help="Records per page (max 500).")
    @click.option("--all", "all_pages", is_flag=True, help="Stream all pages (no buffer).")
    @click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
    @click.option("--filter", "filter_exprs", multiple=True,
                  help="Filter: key=value, '{json}', or @file.json. Repeatable.")
    @click.option("--filter-file", type=click.Path(exists=True),
                  help="Path to filter JSON file.")
    @click.pass_context
    def list_cmd(ctx: click.Context, limit: int, all_pages: bool, output_json: bool,
                 filter_exprs: tuple[str, ...], filter_file: str | None) -> None:
        client: AttioClient = ctx.obj["client"]
        filter_body = build_filter(filter_exprs, filter_file)
        count = 0
        for record in client.list_records(
            object_slug, limit=limit, all_pages=all_pages, filter=filter_body
        ):
            format_output(record, as_json=output_json, stream=True, object_type=object_slug)
            count += 1
        if not all_pages:
            # D-15: show footer — assume has_more=True if we hit exactly the limit
            format_pagination_footer(count, has_more=(count == limit), as_json=output_json)

    @group.command("get", help=f"Get a record by ID.")
    @click.argument("record_id")
    @click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    def get_cmd(ctx: click.Context, record_id: str, output_json: bool) -> None:
        client: AttioClient = ctx.obj["client"]
        result = client.get_record(object_slug, record_id)
        format_output(result, as_json=output_json, object_type=object_slug)

    @group.command("create", help=f"Create a record.")
    @click.option("--values", "values_json", required=True,
                  help='Record values as JSON: \'{"name": [{"value": "..."}]}\'')
    @click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    def create_cmd(ctx: click.Context, values_json: str, output_json: bool) -> None:
        client: AttioClient = ctx.obj["client"]
        try:
            values = json.loads(values_json)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON in --values: {e}") from e
        result = client.create_record(object_slug, values)
        format_output(result, as_json=output_json, object_type=object_slug)

    @group.command("update", help=f"Update a record (PATCH by default, PUT with --overwrite).")
    @click.argument("record_id")
    @click.option("--values", "values_json", required=True,
                  help="Record values as JSON.")
    @click.option("--overwrite", is_flag=True,
                  help="Use PUT (replace multiselect values). Default is PATCH (append).")
    @click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    def update_cmd(ctx: click.Context, record_id: str, values_json: str,
                   overwrite: bool, output_json: bool) -> None:
        client: AttioClient = ctx.obj["client"]
        try:
            values = json.loads(values_json)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON in --values: {e}") from e
        result = client.update_record(object_slug, record_id, values, overwrite=overwrite)
        format_output(result, as_json=output_json, object_type=object_slug)

    @group.command("assert", help=f"Assert (create-or-update) a record.")
    @click.option("--matching-attribute", required=True,
                  help="Attribute slug used to match existing records (e.g. email_addresses).")
    @click.option("--values", "values_json", required=True,
                  help="Record values as JSON.")
    @click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    def assert_cmd(ctx: click.Context, matching_attribute: str, values_json: str,
                   output_json: bool) -> None:
        client: AttioClient = ctx.obj["client"]
        try:
            values = json.loads(values_json)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON in --values: {e}") from e
        result = client.assert_record(object_slug, values, matching_attribute)
        format_output(result, as_json=output_json, object_type=object_slug)

    @group.command("delete", help=f"Delete a record.")
    @click.argument("record_id")
    @click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
    @click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    def delete_cmd(ctx: click.Context, record_id: str, yes: bool, output_json: bool) -> None:
        client: AttioClient = ctx.obj["client"]
        if not yes:
            click.confirm(f"Delete record {record_id}?", abort=True)
        result = client.delete_record(object_slug, record_id)
        format_output(result, as_json=output_json)

    @group.command("search", help=f"Fuzzy search records.")
    @click.argument("query")
    @click.option("--limit", default=25, show_default=True, help="Max results (1-25).")
    @click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    def search_cmd(ctx: click.Context, query: str, limit: int, output_json: bool) -> None:
        client: AttioClient = ctx.obj["client"]
        result = client.search_records([object_slug], query, limit=limit)
        format_output(result, as_json=output_json, object_type=object_slug)

    return group


# ── Standard object groups (D-01) ─────────────────────────────────────────

people = _make_record_group("people", "people", "Manage people records in Attio.")
companies = _make_record_group("companies", "companies", "Manage company records in Attio.")
deals = _make_record_group("deals", "deals", "Manage deal records in Attio.")
users = _make_record_group("users", "users", "Manage user records in Attio.")
workspaces = _make_record_group("workspaces", "workspaces", "Manage workspace records in Attio.")


# ── Generic records group (D-02) ──────────────────────────────────────────
# Explicit commands with object_slug as first argument — no closure tricks.

records_group = click.Group("records", help="Manage records on any object (including custom objects).")


@records_group.command("list")
@click.argument("object_slug")
@click.option("--limit", default=500, show_default=True, help="Records per page (max 500).")
@click.option("--all", "all_pages", is_flag=True, help="Stream all pages.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.option("--filter", "filter_exprs", multiple=True,
              help="Filter expression. Repeatable.")
@click.option("--filter-file", type=click.Path(exists=True),
              help="Path to filter JSON file.")
@click.pass_context
def records_list(ctx: click.Context, object_slug: str, limit: int, all_pages: bool,
                 output_json: bool, filter_exprs: tuple[str, ...],
                 filter_file: str | None) -> None:
    """List records on any object."""
    client: AttioClient = ctx.obj["client"]
    filter_body = build_filter(filter_exprs, filter_file)
    count = 0
    for record in client.list_records(
        object_slug, limit=limit, all_pages=all_pages, filter=filter_body
    ):
        format_output(record, as_json=output_json, stream=True, object_type=object_slug)
        count += 1
    if not all_pages:
        format_pagination_footer(count, has_more=(count == limit), as_json=output_json)


@records_group.command("get")
@click.argument("object_slug")
@click.argument("record_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def records_get(ctx: click.Context, object_slug: str, record_id: str,
                output_json: bool) -> None:
    """Get a record by ID on any object."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_record(object_slug, record_id)
    format_output(result, as_json=output_json, object_type=object_slug)


@records_group.command("create")
@click.argument("object_slug")
@click.option("--values", "values_json", required=True, help="Record values as JSON.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def records_create(ctx: click.Context, object_slug: str, values_json: str,
                   output_json: bool) -> None:
    """Create a record on any object."""
    client: AttioClient = ctx.obj["client"]
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --values: {e}") from e
    result = client.create_record(object_slug, values)
    format_output(result, as_json=output_json, object_type=object_slug)


@records_group.command("update")
@click.argument("object_slug")
@click.argument("record_id")
@click.option("--values", "values_json", required=True, help="Record values as JSON.")
@click.option("--overwrite", is_flag=True,
              help="Use PUT (replace). Default is PATCH (append).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def records_update(ctx: click.Context, object_slug: str, record_id: str,
                   values_json: str, overwrite: bool, output_json: bool) -> None:
    """Update a record on any object (PATCH default, PUT with --overwrite)."""
    client: AttioClient = ctx.obj["client"]
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --values: {e}") from e
    result = client.update_record(object_slug, record_id, values, overwrite=overwrite)
    format_output(result, as_json=output_json, object_type=object_slug)


@records_group.command("assert")
@click.argument("object_slug")
@click.option("--matching-attribute", required=True,
              help="Attribute slug used to match existing records.")
@click.option("--values", "values_json", required=True, help="Record values as JSON.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def records_assert(ctx: click.Context, object_slug: str, matching_attribute: str,
                   values_json: str, output_json: bool) -> None:
    """Assert (create-or-update) a record on any object."""
    client: AttioClient = ctx.obj["client"]
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --values: {e}") from e
    result = client.assert_record(object_slug, values, matching_attribute)
    format_output(result, as_json=output_json, object_type=object_slug)


@records_group.command("delete")
@click.argument("object_slug")
@click.argument("record_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def records_delete(ctx: click.Context, object_slug: str, record_id: str,
                   yes: bool, output_json: bool) -> None:
    """Delete a record on any object."""
    client: AttioClient = ctx.obj["client"]
    if not yes:
        click.confirm(f"Delete {object_slug} record {record_id}?", abort=True)
    result = client.delete_record(object_slug, record_id)
    format_output(result, as_json=output_json)


@records_group.command("search")
@click.argument("object_slug")
@click.argument("query")
@click.option("--limit", default=25, show_default=True, help="Max results (1-25).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def records_search(ctx: click.Context, object_slug: str, query: str,
                   limit: int, output_json: bool) -> None:
    """Fuzzy search records on any object."""
    client: AttioClient = ctx.obj["client"]
    result = client.search_records([object_slug], query, limit=limit)
    format_output(result, as_json=output_json, object_type=object_slug)
