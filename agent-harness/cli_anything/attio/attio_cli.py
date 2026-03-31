"""Root Click group and CLI entry point."""
import sys

import rich_click as click  # rich-click replaces click for styled --help

from .records import companies, deals, people, records_group, users, workspaces
from .utils.attio_client import AttioClient
from .utils.config import load_config
from .utils.exceptions import AttioError


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version="0.1.0", prog_name="attio")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Attio CLI -- full CRM access for AI agents and power users.

    Every Attio API operation is available as a typed, documented command.
    Use --json on any command for agent-consumable output.
    """
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    config = load_config()  # Raises AuthError (exit 4) if key missing
    client = AttioClient(api_key=config.api_key, base_url=config.base_url)
    client.ensure_valid()  # INFRA-02: validate once per session, cached (D-09)
    ctx.obj["client"] = client


# Register all command groups
cli.add_command(people)
cli.add_command(companies)
cli.add_command(deals)
cli.add_command(users)
cli.add_command(workspaces)
cli.add_command(records_group)
