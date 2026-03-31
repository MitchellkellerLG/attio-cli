"""attio config subcommand group -- set/get/path/list config values."""
import os

import click

from .utils.config import CONFIG_FILE, load_config, save_config
from .utils.exceptions import AuthError


def _mask_key(key: str) -> str:
    """Show first 8 chars + '...' for security."""
    if len(key) <= 8:
        return "***"
    return key[:8] + "..."


@click.group("config", help="Manage attio CLI configuration.")
def config_group() -> None:
    pass


@config_group.group("set", help="Set a config value.")
def config_set() -> None:
    pass


@config_set.command("api-key", help="Set the Attio API key.")
@click.argument("api_key")
def set_api_key(api_key: str) -> None:
    """Save API key to ~/.config/attio/config.json (chmod 0o600).

    Note: ATTIO_API_KEY environment variable always takes precedence over this file.
    """
    # Preserve existing base_url if present
    try:
        existing = load_config()
        base_url = existing.base_url if existing.base_url != "https://api.attio.com/v2" else None
    except AuthError:
        base_url = None

    save_config(api_key, base_url)
    click.echo(f"API key saved to {CONFIG_FILE}")
    click.echo(f"Key: {_mask_key(api_key)}")


@config_set.command("base-url", help="Override the Attio API base URL (advanced).")
@click.argument("base_url")
def set_base_url(base_url: str) -> None:
    """Override API base URL. Default: https://api.attio.com/v2"""
    try:
        existing = load_config()
        save_config(existing.api_key, base_url)
        click.echo(f"Base URL set to: {base_url}")
    except AuthError:
        raise click.ClickException(
            "Cannot set base-url: no API key configured.\n"
            "Run: attio config set api-key <your-key>"
        )


@config_group.group("get", help="Get a config value.")
def config_get() -> None:
    pass


@config_get.command("api-key", help="Print the current API key (masked).")
def get_api_key() -> None:
    try:
        config = load_config()
        # Show env var vs file source
        source = "env var (ATTIO_API_KEY)" if os.getenv("ATTIO_API_KEY") else str(CONFIG_FILE)
        click.echo(f"api_key: {_mask_key(config.api_key)}  [from {source}]")
    except AuthError:
        click.echo("api_key: (not set)", err=True)
        raise SystemExit(4)


@config_get.command("base-url", help="Print the current base URL.")
def get_base_url() -> None:
    try:
        config = load_config()
        click.echo(f"base_url: {config.base_url}")
    except AuthError:
        click.echo("base_url: https://api.attio.com/v2 (default -- no config file)")


@config_group.command("path", help="Print the config file path.")
def config_path() -> None:
    click.echo(str(CONFIG_FILE))


@config_group.command("list", help="List all config values.")
def config_list() -> None:
    click.echo(f"Config file: {CONFIG_FILE}")
    try:
        config = load_config()
        source = "env var" if os.getenv("ATTIO_API_KEY") else "file"
        click.echo(f"  api_key:  {_mask_key(config.api_key)}  [{source}]")
        click.echo(f"  base_url: {config.base_url}")
    except AuthError:
        click.echo("  api_key:  (not set)")
        click.echo("  base_url: https://api.attio.com/v2 (default)")
        click.echo("\nRun: attio config set api-key <your-key>")
