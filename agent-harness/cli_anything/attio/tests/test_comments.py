"""Click CliRunner tests for comments and threads command groups."""
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


# ── Comments create ────────────────────────────────────────────────────────

class TestCommentsCreate:
    def test_create_on_record_starts_new_thread(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "comments", "create",
                    "--body", "Looks good to me",
                    "--record-id", "rec_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_comment.assert_called_once_with(
            body="Looks good to me",
            record_id="rec_abc123",
            entry_id=None,
            thread_id=None,
        )

    def test_create_reply_on_thread(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "comments", "create",
                    "--body", "Thanks!",
                    "--thread-id", "thrd_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_comment.assert_called_once_with(
            body="Thanks!",
            record_id=None,
            entry_id=None,
            thread_id="thrd_abc123",
        )

    def test_create_requires_record_or_thread(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["comments", "create", "--body", "Hello", "--json"],
            )
        assert result.exit_code != 0
        mock_client.create_comment.assert_not_called()

    def test_create_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "comments", "create",
                    "--body", "Test",
                    "--record-id", "rec_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["comment_id"] == "cmnt_abc123"


# ── Comments get ───────────────────────────────────────────────────────────

class TestCommentsGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["comments", "get", "cmnt_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["comment_id"] == "cmnt_abc123"
        mock_client.get_comment.assert_called_once_with("cmnt_abc123")


# ── Comments delete ────────────────────────────────────────────────────────

class TestCommentsDelete:
    def test_delete_with_yes_flag(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["comments", "delete", "cmnt_abc123", "--yes", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_comment.assert_called_once_with("cmnt_abc123")

    def test_delete_without_yes_aborts(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["comments", "delete", "cmnt_abc123", "--json"], input="n\n"
            )
        assert result.exit_code != 0
        mock_client.delete_comment.assert_not_called()


# ── Comments resolve ───────────────────────────────────────────────────────

class TestCommentsResolve:
    def test_resolve_calls_client(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["comments", "resolve", "cmnt_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.resolve_comment.assert_called_once_with("cmnt_abc123")

    def test_resolve_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["comments", "resolve", "cmnt_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["comment_id"] == "cmnt_abc123"


# ── Comments unresolve ─────────────────────────────────────────────────────

class TestCommentsUnresolve:
    def test_unresolve_calls_client(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["comments", "unresolve", "cmnt_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.unresolve_comment.assert_called_once_with("cmnt_abc123")


# ── Threads list ───────────────────────────────────────────────────────────

class TestThreadsList:
    def test_list_by_record_id(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["threads", "list", "--record-id", "rec_abc123", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.list_threads.assert_called_once_with(
            record_id="rec_abc123", entry_id=None
        )

    def test_list_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["threads", "list", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data

    def test_list_without_filters(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["threads", "list", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_threads.assert_called_once_with(record_id=None, entry_id=None)


# ── Threads get ────────────────────────────────────────────────────────────

class TestThreadsGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["threads", "get", "thrd_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["thread_id"] == "thrd_abc123"
        mock_client.get_thread.assert_called_once_with("thrd_abc123")

    def test_get_includes_comments(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["threads", "get", "thrd_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "comments" in data
        assert len(data["comments"]) >= 1
