"""Click CliRunner tests for the notes command group."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli


def make_ctx_with_client(mock_client: MagicMock) -> list:
    """Return [load_config patch, AttioClient patch] that inject mock_client."""
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


# ── Notes create ──────────────────────────────────────────────────────────

class TestNotesCreate:
    def test_create_passes_all_args(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "notes", "create",
                    "--parent-object", "people",
                    "--parent-record-id", "rec_abc123",
                    "--title", "Meeting Notes",
                    "--content", "Discussed Q4 goals",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_note.assert_called_once_with(
            parent_object="people",
            parent_record_id="rec_abc123",
            title="Meeting Notes",
            content="Discussed Q4 goals",
            format="plaintext",
        )

    def test_create_returns_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "notes", "create",
                    "--parent-object", "people",
                    "--parent-record-id", "rec_abc123",
                    "--title", "T",
                    "--content", "C",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["note_id"] == "note_abc123"

    def test_create_custom_format(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "notes", "create",
                    "--parent-object", "people",
                    "--parent-record-id", "rec_abc123",
                    "--title", "T",
                    "--content", "C",
                    "--format", "markdown",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.create_note.call_args
        assert kwargs["format"] == "markdown"

    def test_create_missing_required_options(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["notes", "create", "--title", "T"])
        assert result.exit_code != 0


# ── Notes get ─────────────────────────────────────────────────────────────

class TestNotesGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["notes", "get", "note_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_note.assert_called_once_with("note_abc123")

    def test_get_returns_note_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["notes", "get", "note_abc123", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["title"] == "Meeting Notes"


# ── Notes list ────────────────────────────────────────────────────────────

class TestNotesList:
    def test_list_no_filters(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["notes", "list", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_notes.assert_called_once_with(
            parent_object=None,
            parent_record_id=None,
            limit=None,
        )

    def test_list_with_parent_filter(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "notes", "list",
                    "--parent-object", "people",
                    "--parent-record-id", "rec_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.list_notes.assert_called_once_with(
            parent_object="people",
            parent_record_id="rec_abc123",
            limit=None,
        )

    def test_list_returns_valid_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["notes", "list", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert len(data["data"]) == 1


# ── Notes update ──────────────────────────────────────────────────────────

class TestNotesUpdate:
    def test_update_title(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["notes", "update", "note_abc123", "--title", "New Title", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.update_note.assert_called_once_with(
            "note_abc123", title="New Title", content=None
        )

    def test_update_content(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["notes", "update", "note_abc123", "--content", "New content", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.update_note.assert_called_once_with(
            "note_abc123", title=None, content="New content"
        )

    def test_update_returns_note_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["notes", "update", "note_abc123", "--title", "T", "--json"],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["note_id"] == "note_abc123"


# ── Notes delete ──────────────────────────────────────────────────────────

class TestNotesDelete:
    def test_delete_with_yes_flag(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["notes", "delete", "note_abc123", "--yes", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_note.assert_called_once_with("note_abc123")

    def test_delete_without_yes_aborts(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["notes", "delete", "note_abc123", "--json"], input="n\n"
            )
        assert result.exit_code != 0
        mock_client.delete_note.assert_not_called()

    def test_delete_yes_confirms_without_prompt(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["notes", "delete", "note_abc123", "--yes"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_note.assert_called_once_with("note_abc123")
