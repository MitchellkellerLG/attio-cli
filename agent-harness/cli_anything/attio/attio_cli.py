"""Root Click group and CLI entry point."""
import rich_click as click

from .config_cmd import config_group
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

    Shell completion:
      bash:  eval "$(_ATTIO_COMPLETE=bash_source attio)"
      zsh:   eval "$(_ATTIO_COMPLETE=zsh_source attio)"
      fish:  _ATTIO_COMPLETE=fish_source attio | source
    """
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    # Skip auth for config and completion commands (no API key needed)
    if ctx.invoked_subcommand in ("config", "completion"):
        return

    config = load_config()  # Raises AuthError (exit 4) if key missing
    client = AttioClient(api_key=config.api_key, base_url=config.base_url)
    client.ensure_valid()  # INFRA-02: session-cached GET /v2/self (D-09)
    ctx.obj["client"] = client


@cli.command("completion", help="Print shell completion setup instructions.")
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    default="bash",
    show_default=True,
    help="Target shell.",
)
def completion_cmd(shell: str) -> None:
    """Print the eval block to activate shell completion.

    bash:  eval "$(attio completion --shell bash)"
    zsh:   eval "$(attio completion --shell zsh)"
    fish:  attio completion --shell fish | source
    """
    prog_name = "attio"
    if shell == "bash":
        click.echo(f'eval "$(_ATTIO_COMPLETE=bash_source {prog_name})"')
    elif shell == "zsh":
        click.echo(f'eval "$(_ATTIO_COMPLETE=zsh_source {prog_name})"')
    elif shell == "fish":
        click.echo(f"_ATTIO_COMPLETE=fish_source {prog_name} | source")


# Register all command groups
cli.add_command(people)
cli.add_command(companies)
cli.add_command(deals)
cli.add_command(users)
cli.add_command(workspaces)
cli.add_command(records_group)
cli.add_command(config_group)
