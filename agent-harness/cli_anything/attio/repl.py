"""Interactive REPL for the Attio CLI."""
from pathlib import Path

import click
from click_repl import repl as click_repl_run
from prompt_toolkit.history import FileHistory

# click-repl 0.3.0 sets group_ctx.protected_args directly, but Click 8.3+
# made protected_args a read-only deprecated property (backing attr is _protected_args).
# Restore the setter so click-repl can dispatch commands correctly.
_orig_protected_args_prop = click.Context.__dict__.get("protected_args")
if _orig_protected_args_prop is not None and _orig_protected_args_prop.fset is None:
    click.Context.protected_args = property(
        _orig_protected_args_prop.fget,
        lambda self, v: setattr(self, "_protected_args", v),
    )


def _ensure_history_dir() -> str:
    """Create ~/.config/attio/ if needed and return the history file path."""
    history_dir = Path.home() / ".config" / "attio"
    history_dir.mkdir(parents=True, exist_ok=True)
    return str(history_dir / "history")


def register_repl_command(cli_group: click.Group) -> None:
    """Register the `repl` subcommand on cli_group with persistent FileHistory."""

    @cli_group.command("repl")
    @click.pass_context
    def repl_cmd(ctx: click.Context) -> None:
        """Start an interactive REPL session with persistent history.

        Arrow-up/down for history, Tab for completion, Ctrl-D or :quit to exit.
        Type any attio subcommand at the prompt. Example: people list --json
        """
        prompt_kwargs: dict = {
            "history": FileHistory(_ensure_history_dir()),
            "message": "attio> ",
        }
        click_repl_run(ctx, prompt_kwargs=prompt_kwargs)
