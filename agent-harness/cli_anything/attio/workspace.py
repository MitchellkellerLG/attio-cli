"""Workspace command group: workspace members and self-identification (read-only)."""
from __future__ import annotations

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


workspace_group = click.Group("workspace", help="Workspace information and members.")


@workspace_group.command("members", help="List all workspace members.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def members_cmd(ctx: click.Context, output_json: bool) -> None:
    """List all members in the current workspace."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_workspace_members()
    format_output(result, as_json=output_json)


@workspace_group.command("member", help="Get a workspace member by ID.")
@click.argument("member_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def member_cmd(ctx: click.Context, member_id: str, output_json: bool) -> None:
    """Get a single workspace member by their ID."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_workspace_member(member_id)
    format_output(result, as_json=output_json)


@workspace_group.command("self", help="Show current workspace and token info.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def self_cmd(ctx: click.Context, output_json: bool) -> None:
    """Display information about the current token and workspace."""
    client: AttioClient = ctx.obj["client"]
    result = client.self_check()
    format_output(result, as_json=output_json)
