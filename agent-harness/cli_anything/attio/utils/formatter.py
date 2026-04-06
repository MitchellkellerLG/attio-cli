"""Output formatter — Rich tables and JSON. All output passes through here."""
import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table

_console = Console()
_err_console = Console(stderr=True)

# Default columns per object type (Claude's discretion)
_DEFAULT_COLUMNS: dict[str, list[str]] = {
    "people": ["name", "email_addresses", "phone_numbers"],
    "companies": ["name", "domains"],
    "deals": ["name", "stage", "value"],
    "users": ["name", "email_addresses"],
    "workspaces": ["name", "domains"],
}
_FALLBACK_COLUMNS = 3  # Show first N value keys for unknown object types


def _is_json_mode(as_json: bool) -> bool:
    """True if output should be raw JSON (flag forced or piped)."""
    return as_json or not sys.stdout.isatty()


def _extract_display_value(values: list[dict[str, Any]]) -> str:
    """Pull the first human-readable value from an Attio multi-value attribute list."""
    if not values:
        return ""
    v = values[0]
    # Try common value keys in priority order
    for key in ("value", "email_address", "phone_number", "domain", "original_value"):
        if key in v:
            return str(v[key])
    return str(next(iter(v.values()), ""))


def _render_record_table(records: list[dict[str, Any]], object_type: str | None) -> None:
    """Render a Rich table for one or more records."""
    if not records:
        _console.print("[dim](no records)[/dim]")
        return

    columns = _DEFAULT_COLUMNS.get(object_type or "", [])
    sample_values = records[0].get("values", {})

    if not columns:
        # Fallback: first N keys from the sample record's values
        columns = list(sample_values.keys())[:_FALLBACK_COLUMNS]

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("record_id", style="dim", no_wrap=True)
    for col in columns:
        table.add_column(col)

    for record in records:
        record_id = record.get("id", {}).get("record_id", "—")
        values = record.get("values", {})
        row = [record_id]
        for col in columns:
            attr_values = values.get(col, [])
            row.append(_extract_display_value(attr_values) if attr_values else "—")
        table.add_row(*row)

    _console.print(table)


def format_output(
    data: dict[str, Any] | list[dict[str, Any]],
    as_json: bool,
    stream: bool = False,
    object_type: str | None = None,
) -> None:
    """Single entry point for all data output. Commands never call json.dumps directly.

    - as_json=True or sys.stdout.isatty()==False → JSON to stdout
    - as_json=False and TTY → Rich table to stdout
    - stream=True → used during --all pagination; print each record as it arrives
    """
    if _is_json_mode(as_json):
        click.echo(json.dumps(data, indent=2, default=str))
        return

    # TTY mode — render Rich table
    records = data if isinstance(data, list) else [data]
    _render_record_table(records, object_type)


def format_error(message: str, hint: str | None = None) -> None:
    """Write error to stderr. Never touches stdout."""
    _err_console.print(f"[red]Error:[/red] {message}")
    if hint:
        _err_console.print(f"[dim]Hint: {hint}[/dim]")


def format_pagination_footer(count: int, has_more: bool, as_json: bool) -> None:
    """D-15: footer after partial results. Suppressed in JSON mode to avoid breaking jq pipes."""
    if _is_json_mode(as_json):
        # Never emit footer in JSON/pipe mode — agents count records themselves
        return
    if has_more:
        click.echo(f"(showing {count} results — use --all to fetch all pages)")
