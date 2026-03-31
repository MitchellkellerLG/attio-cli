"""Meetings command group: view meetings and recordings (read-only)."""
from __future__ import annotations

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


meetings_group = click.Group("meetings", help="View meetings and recordings (read-only).")


@meetings_group.command("list", help="List all meetings.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def list_cmd(ctx: click.Context, output_json: bool) -> None:
    """List all meetings in the workspace."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_meetings()
    format_output(result, as_json=output_json)


@meetings_group.command("get", help="Get a meeting by ID.")
@click.argument("meeting_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def get_cmd(ctx: click.Context, meeting_id: str, output_json: bool) -> None:
    """Get a meeting by its ID."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_meeting(meeting_id)
    format_output(result, as_json=output_json)


@meetings_group.command("recordings", help="List recordings for a meeting.")
@click.argument("meeting_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def recordings_cmd(ctx: click.Context, meeting_id: str, output_json: bool) -> None:
    """List all recordings for the specified meeting."""
    client: AttioClient = ctx.obj["client"]
    result = client.list_meeting_recordings(meeting_id)
    format_output(result, as_json=output_json)


@meetings_group.command("transcript", help="Get the transcript for a recording.")
@click.argument("meeting_id")
@click.argument("recording_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def transcript_cmd(
    ctx: click.Context, meeting_id: str, recording_id: str, output_json: bool
) -> None:
    """Get the transcript for a specific recording."""
    client: AttioClient = ctx.obj["client"]
    result = client.get_meeting_transcript(meeting_id, recording_id)
    format_output(result, as_json=output_json)
