"""Objects command group — manage Attio object types (metadata)."""
from __future__ import annotations

import json
from typing import Any

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


objects_group = click.Group("objects", help="Manage Attio object types (metadata).")


@objects_group.command("list", help="List all object types.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def objects_list(ctx: click.Context, output_json: bool) -> None:
    """List all Attio object types."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_objects()
    format_output(result, as_json=output_json)


@objects_group.command("get", help="Get an object type by ID or slug.")
@click.argument("object_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def objects_get(ctx: click.Context, object_id: str, output_json: bool) -> None:
    """Get an Attio object type by ID or slug."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_object(object_id)
    format_output(result, as_json=output_json)


@objects_group.command("create", help="Create a custom object type.")
@click.option("--slug", required=True, help="API slug for the object (e.g. custom_thing).")
@click.option("--singular", required=True, help="Singular noun (e.g. Thing).")
@click.option("--plural", required=True, help="Plural noun (e.g. Things).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def objects_create(
    ctx: click.Context, slug: str, singular: str, plural: str, output_json: bool
) -> None:
    """Create a custom Attio object type."""
    client: AttioClient = ctx.obj["client"]
    result = client.create_object(api_slug=slug, singular_noun=singular, plural_noun=plural)
    format_output(result, as_json=output_json)


@objects_group.command("update", help="Update an object type.")
@click.argument("object_id")
@click.option("--data", "data_json", required=True, help="Update fields as JSON string.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def objects_update(ctx: click.Context, object_id: str, data_json: str, output_json: bool) -> None:
    """Update an Attio object type."""
    client: AttioClient = ctx.obj["client"]
    try:
        data: dict[str, Any] = json.loads(data_json)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --data: {e}") from e
    result = client.update_object(object_id, data)
    format_output(result, as_json=output_json)


@objects_group.command("views", help="List views for an object.")
@click.argument("object_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def objects_views(ctx: click.Context, object_id: str, output_json: bool) -> None:
    """List views for an Attio object type."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_object_views(object_id)
    format_output(result, as_json=output_json)
