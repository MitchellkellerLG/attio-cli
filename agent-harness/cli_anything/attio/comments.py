"""Comments and threads command groups."""
from __future__ import annotations

import click

from .utils.attio_client import AttioClient
from .utils.formatter import format_output


# ── Comments group ─────────────────────────────────────────────────────────

comments_group = click.Group("comments", help="Manage comments on threads/records.")


@comments_group.command("create", help="Create a comment on a record or thread.")
@click.option("--body", required=True, help="Comment body text.")
@click.option("--record-id", default=None, help="Record ID to attach comment to (starts new thread).")
@click.option("--entry-id", default=None, help="List entry ID to attach comment to.")
@click.option("--thread-id", default=None, help="Existing thread ID to reply to.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def comments_create(
    ctx: click.Context,
    body: str,
    record_id: str | None,
    entry_id: str | None,
    thread_id: str | None,
    output_json: bool,
) -> None:
    """Create a comment. Provide --record-id to start a new thread or --thread-id to reply."""
    if not record_id and not thread_id:
        raise click.ClickException("Must provide either --record-id (new thread) or --thread-id (reply).")
    client: AttioClient = ctx.obj["client"]
    result = client.create_comment(
        body=body,
        record_id=record_id,
        entry_id=entry_id,
        thread_id=thread_id,
    )
    format_output(result, as_json=output_json)


@comments_group.command("get", help="Get a comment by ID.")
@click.argument("comment_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def comments_get(ctx: click.Context, comment_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.get_comment(comment_id)
    format_output(result, as_json=output_json)


@comments_group.command("delete", help="Delete a comment by ID.")
@click.argument("comment_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def comments_delete(ctx: click.Context, comment_id: str, yes: bool, output_json: bool) -> None:
    if not yes:
        click.confirm(f"Delete comment {comment_id}?", abort=True)
    client: AttioClient = ctx.obj["client"]
    result = client.delete_comment(comment_id)
    format_output(result, as_json=output_json)


@comments_group.command("resolve", help="Resolve the thread for a comment.")
@click.argument("comment_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def comments_resolve(ctx: click.Context, comment_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.resolve_comment(comment_id)
    format_output(result, as_json=output_json)


@comments_group.command("unresolve", help="Unresolve the thread for a comment.")
@click.argument("comment_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def comments_unresolve(ctx: click.Context, comment_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.unresolve_comment(comment_id)
    format_output(result, as_json=output_json)


# ── Threads group ──────────────────────────────────────────────────────────

threads_group = click.Group("threads", help="Manage comment threads.")


@threads_group.command("list", help="List threads on a record or entry.")
@click.option("--record-id", default=None, help="Filter by record ID.")
@click.option("--entry-id", default=None, help="Filter by list entry ID.")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def threads_list(
    ctx: click.Context,
    record_id: str | None,
    entry_id: str | None,
    output_json: bool,
) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.list_threads(record_id=record_id, entry_id=entry_id)
    format_output(result, as_json=output_json)


@threads_group.command("get", help="Get a thread by ID (includes all comments).")
@click.argument("thread_id")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def threads_get(ctx: click.Context, thread_id: str, output_json: bool) -> None:
    client: AttioClient = ctx.obj["client"]
    result = client.get_thread(thread_id)
    format_output(result, as_json=output_json)
