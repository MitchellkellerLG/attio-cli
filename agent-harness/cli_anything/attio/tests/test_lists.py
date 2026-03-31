"""Click CliRunner tests for the lists command group."""
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


# ── Lists list ────────────────────────────────────────────────────────────

class TestListsList:
    def test_list_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["lists", "list", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert data["data"][0]["name"] == "Sales Pipeline"

    def test_list_calls_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["lists", "list", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_lists.assert_called_once()


# ── Lists get ─────────────────────────────────────────────────────────────

class TestListsGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["lists", "get", "list_abc123", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["name"] == "Sales Pipeline"
        mock_client.get_list.assert_called_once_with("list_abc123")

    def test_get_passes_list_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(cli, ["lists", "get", "my_list_id", "--json"])
        args, kwargs = mock_client.get_list.call_args
        assert args[0] == "my_list_id" or kwargs.get("list_id") == "my_list_id"


# ── Lists create ──────────────────────────────────────────────────────────

class TestListsCreate:
    def test_create_passes_name_and_parent(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["lists", "create", "--name", "Sales Pipeline", "--parent-object", "companies", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_list.assert_called_once()
        args, kwargs = mock_client.create_list.call_args
        name_used = kwargs.get("name") or args[0]
        parent_used = kwargs.get("parent_object") or args[1]
        assert name_used == "Sales Pipeline"
        assert parent_used == "companies"

    def test_create_returns_list(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["lists", "create", "--name", "Test", "--parent-object", "people", "--json"],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["list_id"] == "list_abc123"


# ── Lists update ──────────────────────────────────────────────────────────

class TestListsUpdate:
    def test_update_passes_id_and_name(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["lists", "update", "list_abc123", "--name", "New Name", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.update_list.assert_called_once()
        args, kwargs = mock_client.update_list.call_args
        list_id_used = kwargs.get("list_id") or args[0]
        name_used = kwargs.get("name") or args[1]
        assert list_id_used == "list_abc123"
        assert name_used == "New Name"


# ── Lists views ───────────────────────────────────────────────────────────

class TestListsViews:
    def test_views_calls_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["lists", "views", "list_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_list_views.assert_called_once()
        args, kwargs = mock_client.list_list_views.call_args
        list_id_used = kwargs.get("list_id") or args[0]
        assert list_id_used == "list_abc123"

    def test_views_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["lists", "views", "list_abc123", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert data["data"][0]["name"] == "Default View"
