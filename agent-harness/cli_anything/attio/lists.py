"""Lists command group: manage Attio lists."""
from __future__ import annotations

from typing import Any

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


@click.group("lists", help="Manage Attio lists.")
def lists_group() -> None:
    pass


@lists_group.command("list", help="List all lists.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def lists_list(ctx: click.Context, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.list_lists()
    format_output(result, as_json=output_json)


@lists_group.command("get", help="Get a list by ID.")
@click.argument("list_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def lists_get(ctx: click.Context, list_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.get_list(list_id)
    format_output(result, as_json=output_json)


@lists_group.command("create", help="Create a list.")
@click.option("--name", required=True, help="Name of the list.")
@click.option("--parent-object", required=True, help="Parent object slug (e.g. people, companies).")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def lists_create(ctx: click.Context, name: str, parent_object: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.create_list(name=name, parent_object=parent_object)
    format_output(result, as_json=output_json)


@lists_group.command("update", help="Update a list.")
@click.argument("list_id")
@click.option("--name", required=True, help="New name for the list.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def lists_update(ctx: click.Context, list_id: str, name: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.update_list(list_id=list_id, name=name)
    format_output(result, as_json=output_json)


@lists_group.command("views", help="List views for a list.")
@click.argument("list_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def lists_views(ctx: click.Context, list_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.list_list_views(list_id=list_id)
    format_output(result, as_json=output_json)
