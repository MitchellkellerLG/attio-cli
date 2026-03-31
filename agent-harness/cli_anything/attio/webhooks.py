"""Webhooks command group: manage Attio webhook subscriptions (full CRUD)."""
from __future__ import annotations

import json

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


webhooks_group = click.Group("webhooks", help="Manage webhook subscriptions.")


@webhooks_group.command("create", help="Create a webhook subscription.")
@click.option("--target-url", required=True, help="URL that Attio will POST events to.")
@click.option(
    "--subscriptions",
    required=True,
    help='JSON array of subscription objects, e.g. \'[{"event_type": "record.created"}]\'',
)
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def create_cmd(
    ctx: click.Context, target_url: str, subscriptions: str, output_json: bool
) -> None:
    """Create a new webhook subscription."""
    client: AttioClient = ctx.obj["client"]
    try:
        subs = json.loads(subscriptions)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --subscriptions: {e}") from e
    result = client.create_webhook(target_url, subs)
    format_output(result, as_json=output_json)


@webhooks_group.command("get", help="Get a webhook by ID.")
@click.argument("webhook_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def get_cmd(ctx: click.Context, webhook_id: str, output_json: bool) -> None:
    """Get a webhook subscription by its ID."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_webhook(webhook_id)
    format_output(result, as_json=output_json)


@webhooks_group.command("list", help="List all webhook subscriptions.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def list_cmd(ctx: click.Context, output_json: bool) -> None:
    """List all configured webhook subscriptions."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_webhooks()
    format_output(result, as_json=output_json)


@webhooks_group.command("update", help="Update a webhook subscription.")
@click.argument("webhook_id")
@click.option(
    "--data",
    "data_json",
    required=True,
    help='JSON object with fields to update, e.g. \'{"status": "paused"}\'',
)
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def update_cmd(
    ctx: click.Context, webhook_id: str, data_json: str, output_json: bool
) -> None:
    """Update a webhook subscription (target_url, subscriptions, or status)."""
    client: AttioClient = ctx.obj["client"]
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in --data: {e}") from e
    result = client.update_webhook(webhook_id, data)
    format_output(result, as_json=output_json)


@webhooks_group.command("delete", help="Delete a webhook subscription.")
@click.argument("webhook_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def delete_cmd(
    ctx: click.Context, webhook_id: str, yes: bool, output_json: bool
) -> None:
    """Delete a webhook subscription permanently."""
    client: AttioClient = ctx.obj["client"]
    if not yes:
        click.confirm(f"Delete webhook {webhook_id}?", abort=True)
    result = client.delete_webhook(webhook_id)
    format_output(result, as_json=output_json)
