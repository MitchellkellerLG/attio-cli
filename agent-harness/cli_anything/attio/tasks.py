"""Tasks command group — manage tasks with assignees and linked records."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output

tasks_group = click.Group("tasks", help="Manage tasks.")


@tasks_group.command("create", help="Create a task.")
@click.option("--content", required=True, help="Task content/description.")
@click.option("--deadline", "deadline_at", default=None,
              help="Deadline in ISO 8601 format (e.g. 2026-04-15T00:00:00.000Z).")
@click.option("--assignee", "assignees", multiple=True,
              help='Assignee as JSON: \'{"referenced_actor_type":"workspace-member","referenced_actor_id":"..."}\'. Repeatable.')
@click.option("--linked-record", "linked_records", multiple=True,
              help='Linked record as JSON: \'{"target_object":"people","target_record_id":"..."}\'. Repeatable.')
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def tasks_create(
    ctx: click.Context,
    content: str,
    deadline_at: str | None,
    assignees: tuple[str, ...],
    linked_records: tuple[str, ...],
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]

    parsed_assignees: list[dict[str, Any]] | None = None
    if assignees:
        try:
            parsed_assignees = [json.loads(a) for a in assignees]
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON in --assignee: {e}") from e

    parsed_linked: list[dict[str, Any]] | None = None
    if linked_records:
        try:
            parsed_linked = [json.loads(r) for r in linked_records]
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON in --linked-record: {e}") from e

    # Attio requires deadline_at; default to 7 days from now if not provided.
    effective_deadline = deadline_at or (
        datetime.now(timezone.utc) + timedelta(days=7)
    ).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    result = client.create_task(
        content=content,
        deadline_at=effective_deadline,
        assignees=parsed_assignees,
        linked_records=parsed_linked,
    )
    format_output(result, as_json=output_json)


@tasks_group.command("get", help="Get a task by ID.")
@click.argument("task_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def tasks_get(ctx: click.Context, task_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.get_task(task_id)
    format_output(result, as_json=output_json)


@tasks_group.command("list", help="List tasks with optional filters.")
@click.option("--linked-object", default=None, help="Filter by linked object slug.")
@click.option("--linked-record-id", default=None, help="Filter by linked record ID.")
@click.option("--assignee", default=None, help="Filter by assignee actor ID.")
@click.option("--completed/--not-completed", "is_completed", default=None,
              help="Filter by completion status.")
@click.option("--limit", default=None, type=int, help="Maximum number of tasks to return.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def tasks_list(
    ctx: click.Context,
    linked_object: str | None,
    linked_record_id: str | None,
    assignee: str | None,
    is_completed: bool | None,
    limit: int | None,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.list_tasks(
        linked_object=linked_object,
        linked_record_id=linked_record_id,
        assignee=assignee,
        is_completed=is_completed,
        limit=limit,
    )
    format_output(result, as_json=output_json)


@tasks_group.command("update", help="Update a task.")
@click.argument("task_id")
@click.option("--content", default=None, help="New task content.")
@click.option("--deadline", "deadline_at", default=None, help="New deadline (ISO 8601).")
@click.option("--completed/--not-completed", "is_completed", default=None,
              help="Mark task completed or not.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def tasks_update(
    ctx: click.Context,
    task_id: str,
    content: str | None,
    deadline_at: str | None,
    is_completed: bool | None,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.update_task(
        task_id,
        content=content,
        deadline_at=deadline_at,
        is_completed=is_completed,
    )
    format_output(result, as_json=output_json)


@tasks_group.command("delete", help="Delete a task.")
@click.argument("task_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def tasks_delete(ctx: click.Context, task_id: str, yes: bool, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    if not yes:
        click.confirm(f"Delete task {task_id}?", abort=True)
    result = client.delete_task(task_id)
    format_output(result, as_json=output_json)
