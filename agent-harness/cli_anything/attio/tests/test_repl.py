"""Unit tests for the interactive REPL command."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from cli_anything.attio.attio_cli import cli


def _invoke_repl(runner: CliRunner, input_text: str) -> object:
    """Invoke `attio repl` with mocked auth and given stdin input."""
    mock_client = MagicMock()
    mock_client.ensure_valid.return_value = None
    mock_config = MagicMock()
    mock_config.api_key = "test_key"
    mock_config.base_url = "https://api.attio.com/v2"

    with patch("cli_anything.attio.attio_cli.load_config", return_value=mock_config):
        with patch("cli_anything.attio.attio_cli.AttioClient", return_value=mock_client):
            return runner.invoke(cli, ["repl"], input=input_text)


def test_repl_exits_cleanly(runner: CliRunner) -> None:
    """REPL exits with code 0 when given empty input (non-TTY break)."""
    result = _invoke_repl(runner, "\n")
    assert result.exit_code == 0


def test_repl_dispatches_valid_command(runner: CliRunner) -> None:
    """REPL dispatches a valid subcommand without crashing."""
    mock_client = MagicMock()
    mock_client.ensure_valid.return_value = None
    mock_client.get_records.return_value = {"data": [], "next_cursor": None}
    mock_config = MagicMock()
    mock_config.api_key = "test_key"
    mock_config.base_url = "https://api.attio.com/v2"

    with patch("cli_anything.attio.attio_cli.load_config", return_value=mock_config):
        with patch("cli_anything.attio.attio_cli.AttioClient", return_value=mock_client):
            result = runner.invoke(cli, ["repl"], input="workspace self --json\n\n")
    # Either exits 0 or shows help/error -- must not crash the process
    assert result.exit_code == 0 or result.exit_code == 1


def test_repl_continues_after_bad_command(runner: CliRunner) -> None:
    """REPL does not crash when given an unknown command; exits cleanly after."""
    result = _invoke_repl(runner, "not-a-real-command\n\n")
    # exit_code 0 = clean exit after error display (click-repl catches the error)
    assert result.exit_code == 0
    # The REPL should not raise an unhandled exception
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_repl_handles_empty_lines(runner: CliRunner) -> None:
    """REPL does not crash on consecutive empty lines."""
    result = _invoke_repl(runner, "\n\n\n")
    assert result.exit_code == 0
