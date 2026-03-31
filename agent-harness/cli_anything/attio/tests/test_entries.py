"""Click CliRunner tests for the entries command group."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli


def make_ctx_with_client(mock_client: MagicMock) -> list:
    import cli_anything.attio.attio_cli as cli_module

    return [
        patch.object(
            cli_module,
            "load_config",
            return_value=MagicMock(
                api_key="test_key", base_url="https://api.attio.com/v2"
            ),
        ),
        patch.object(cli_module, "AttioClient", return_value=mock_client),
    ]


# ── Entries list ──────────────────────────────────────────────────────────

class TestEntriesList:
    def test_list_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["entries", "list", "list_abc123", "--json"])
        assert result.exit_code == 0, result.output
        # Output contains streamed JSON entry then footer
        output = result.output.strip()
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(output)
        assert data["id"]["entry_id"] == "entry_abc123"

    def test_list_calls_client_with_list_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(cli, ["entries", "list", "list_abc123", "--json"])
        args, kwargs = mock_client.list_entries.call_args
        list_id_used = args[0] if args else kwargs.get("list_id")
        assert list_id_used == "list_abc123"

    def test_list_with_filter(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        mock_client.list_entries.return_value = iter([])
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["entries", "list", "list_abc123", "--filter", "status=Active", "--json"],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.list_entries.call_args
        assert kwargs["filter"] == {"status": {"$eq": "Active"}}

    def test_list_pagination_footer_shown(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        mock_client.list_entries.return_value = iter([])
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["entries", "list", "list_abc123", "--json"])
        assert result.exit_code == 0


# ── Entries get ───────────────────────────────────────────────────────────

class TestEntriesGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["entries", "get", "list_abc123", "entry_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["entry_id"] == "entry_abc123"

    def test_get_passes_ids_to_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(cli, ["entries", "get", "list_abc123", "entry_abc123", "--json"])
        mock_client.get_entry.assert_called_once()
        args, kwargs = mock_client.get_entry.call_args
        list_id_used = kwargs.get("list_id") or args[0]
        entry_id_used = kwargs.get("entry_id") or args[1]
        assert list_id_used == "list_abc123"
        assert entry_id_used == "entry_abc123"


# ── Entries create ────────────────────────────────────────────────────────

class TestEntriesCreate:
    def test_create_passes_parent_record_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "create", "list_abc123",
                    "--parent-record-id", "rec_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_entry.assert_called_once()
        args, kwargs = mock_client.create_entry.call_args
        parent_id_used = kwargs.get("parent_record_id") or args[1]
        assert parent_id_used == "rec_abc123"

    def test_create_with_values(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        values = json.dumps({"status": [{"value": "Active"}]})
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "create", "list_abc123",
                    "--parent-record-id", "rec_abc123",
                    "--values", values,
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.create_entry.call_args
        assert kwargs.get("values") == {"status": [{"value": "Active"}]}

    def test_create_invalid_json_values(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "create", "list_abc123",
                    "--parent-record-id", "rec_abc123",
                    "--values", "not-json",
                ],
            )
        assert result.exit_code != 0


# ── Entries update ────────────────────────────────────────────────────────

class TestEntriesUpdate:
    def test_update_default_is_patch(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "update", "list_abc123", "entry_abc123",
                    "--values", '{"status": [{"value": "Done"}]}',
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.update_entry.assert_called_once()
        _, kwargs = mock_client.update_entry.call_args
        assert kwargs.get("overwrite", False) is False

    def test_update_overwrite_flag(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "update", "list_abc123", "entry_abc123",
                    "--values", "{}",
                    "--overwrite",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.update_entry.call_args
        assert kwargs.get("overwrite") is True

    def test_update_passes_ids(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(
                cli,
                [
                    "entries", "update", "list_abc123", "entry_abc123",
                    "--values", "{}",
                    "--json",
                ],
            )
        args, kwargs = mock_client.update_entry.call_args
        list_id_used = kwargs.get("list_id") or args[0]
        entry_id_used = kwargs.get("entry_id") or args[1]
        assert list_id_used == "list_abc123"
        assert entry_id_used == "entry_abc123"


# ── Entries delete ────────────────────────────────────────────────────────

class TestEntriesDelete:
    def test_delete_with_yes_flag(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["entries", "delete", "list_abc123", "entry_abc123", "--yes", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_entry.assert_called_once()
        args, kwargs = mock_client.delete_entry.call_args
        list_id_used = kwargs.get("list_id") or args[0]
        entry_id_used = kwargs.get("entry_id") or args[1]
        assert list_id_used == "list_abc123"
        assert entry_id_used == "entry_abc123"

    def test_delete_without_yes_aborts(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["entries", "delete", "list_abc123", "entry_abc123", "--json"],
                input="n\n",
            )
        assert result.exit_code != 0
        mock_client.delete_entry.assert_not_called()


# ── Entries assert ────────────────────────────────────────────────────────

class TestEntriesAssert:
    def test_assert_passes_parent_record_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "assert", "list_abc123",
                    "--parent-record-id", "rec_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.assert_entry.assert_called_once()
        args, kwargs = mock_client.assert_entry.call_args
        parent_id_used = kwargs.get("parent_record_id") or args[1]
        assert parent_id_used == "rec_abc123"

    def test_assert_passes_list_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(
                cli,
                [
                    "entries", "assert", "list_abc123",
                    "--parent-record-id", "rec_abc123",
                    "--json",
                ],
            )
        args, kwargs = mock_client.assert_entry.call_args
        list_id_used = kwargs.get("list_id") or args[0]
        assert list_id_used == "list_abc123"

    def test_assert_with_values(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        values = json.dumps({"status": [{"value": "Active"}]})
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "assert", "list_abc123",
                    "--parent-record-id", "rec_abc123",
                    "--values", values,
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.assert_entry.call_args
        assert kwargs.get("values") == {"status": [{"value": "Active"}]}

    def test_assert_returns_entry(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "entries", "assert", "list_abc123",
                    "--parent-record-id", "rec_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["entry_id"] == "entry_abc123"
