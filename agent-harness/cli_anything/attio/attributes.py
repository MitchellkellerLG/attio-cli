"""Attributes command group — manage attributes on Attio objects and lists."""
from __future__ import annotations

import json
from typing import Any

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


attributes_group = click.Group("attributes", help="Manage attributes on objects and lists.")


@attributes_group.command("list", help="List attributes on an object or list.")
@click.option("--object", "object_slug", default=None, help="Object slug or ID.")
@click.option("--list", "list_id", default=None, help="List ID (alternative scope to --object).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_list(
    ctx: click.Context, object_slug: str | None, list_id: str | None, output_json: bool
) -> None:
    """List attributes on an object or list."""
    client: AttioClient = ctx.obj["client"]
    if list_id:
        result = client.list_attributes(list_id, target_type="lists")
    elif object_slug:
        result = client.list_attributes(object_slug, target_type="objects")
    else:
        raise click.ClickException("Provide --object <slug> or --list <id>.")
    format_output(result, as_json=output_json)


@attributes_group.command("get", help="Get an attribute by object and attribute slug.")
@click.argument("object_slug")
@click.argument("attribute_slug")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_get(
    ctx: click.Context, object_slug: str, attribute_slug: str, output_json: bool
) -> None:
    """Get an attribute on an Attio object."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_attribute(object_slug, attribute_slug)
    format_output(result, as_json=output_json)


@attributes_group.command("create", help="Create an attribute on an object.")
@click.option("--object", "object_slug", required=True, help="Object slug.")
@click.option("--title", required=True, help="Attribute display title.")
@click.option("--slug", required=True, help="Attribute API slug.")
@click.option("--type", "attr_type", required=True,
              help="Attribute type (e.g. text, number, select, email, date).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_create(
    ctx: click.Context,
    object_slug: str,
    title: str,
    slug: str,
    attr_type: str,
    output_json: bool,
) -> None:
    """Create an attribute on an Attio object."""
    client: AttioClient = ctx.obj["client"]
    result = client.create_attribute(
        object_slug=object_slug, title=title, api_slug=slug, type=attr_type
    )
    format_output(result, as_json=output_json)


@attributes_group.command("update", help="Update an attribute.")
@click.argument("object_slug")
@click.argument("attribute_slug")
@click.option("--data", "data_json", required=True, help="Update fields as JSON string.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_update(
    ctx: click.Context,
    object_slug: str,
    attribute_slug: str,
    data_json: str,
    output_json: bool,
) -> None:
    """Update an attribute on an Attio object."""
    client: AttioClient = ctx.obj["client"]
    try:
        data: dict[str, Any] = json.loads(data_json)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --data: {e}") from e
    result = client.update_attribute(object_slug, attribute_slug, data)
    format_output(result, as_json=output_json)


@attributes_group.command("archive", help="Archive an attribute (not delete — archive is permanent).")
@click.argument("object_slug")
@click.argument("attribute_slug")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_archive(
    ctx: click.Context,
    object_slug: str,
    attribute_slug: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Archive an attribute on an Attio object.

    WARNING: This archives (not deletes) the attribute. Archiving is permanent
    and cannot be undone through the CLI.
    """
    client: AttioClient = ctx.obj["client"]
    if not yes:
        click.confirm(
            f"Archive attribute '{attribute_slug}' on '{object_slug}'? This cannot be undone.",
            abort=True,
        )
    result = client.archive_attribute(object_slug, attribute_slug)
    format_output(result, as_json=output_json)


@attributes_group.command("options", help="List select options for an attribute.")
@click.argument("object_slug")
@click.argument("attribute_slug")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_options(
    ctx: click.Context, object_slug: str, attribute_slug: str, output_json: bool
) -> None:
    """List select options for a select-type attribute."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_attribute_options(object_slug, attribute_slug)
    format_output(result, as_json=output_json)


@attributes_group.command("options-create", help="Add a select option to an attribute.")
@click.argument("object_slug")
@click.argument("attribute_slug")
@click.option("--title", required=True, help="Option title.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_options_create(
    ctx: click.Context,
    object_slug: str,
    attribute_slug: str,
    title: str,
    output_json: bool,
) -> None:
    """Create a select option on a select-type attribute."""
    client: AttioClient = ctx.obj["client"]
    result = client.create_attribute_option(object_slug, attribute_slug, title)
    format_output(result, as_json=output_json)


@attributes_group.command("statuses", help="List status values for an attribute.")
@click.argument("object_slug")
@click.argument("attribute_slug")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_statuses(
    ctx: click.Context, object_slug: str, attribute_slug: str, output_json: bool
) -> None:
    """List status values for a status-type attribute."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_attribute_statuses(object_slug, attribute_slug)
    format_output(result, as_json=output_json)


@attributes_group.command("statuses-create", help="Add a status value to an attribute.")
@click.argument("object_slug")
@click.argument("attribute_slug")
@click.option("--title", required=True, help="Status value title.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def attributes_statuses_create(
    ctx: click.Context,
    object_slug: str,
    attribute_slug: str,
    title: str,
    output_json: bool,
) -> None:
    """Create a status value on a status-type attribute."""
    client: AttioClient = ctx.obj["client"]
    result = client.create_attribute_status(object_slug, attribute_slug, title)
    format_output(result, as_json=output_json)
