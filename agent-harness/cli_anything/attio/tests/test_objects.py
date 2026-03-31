"""Click CliRunner tests for the objects command group."""
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
            return_value=MagicMock(api_key="test_key", base_url="https://api.attio.com/v2"),
        ),
        patch.object(cli_module, "AttioClient", return_value=mock_client),
    ]


# ── Objects list ──────────────────────────────────────────────────────────

class TestObjectsList:
    def test_list_returns_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["objects", "list", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data

    def test_list_calls_list_objects(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(cli, ["objects", "list", "--json"])
        mock_client.list_objects.assert_called_once()


# ── Objects get ───────────────────────────────────────────────────────────

class TestObjectsGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["objects", "get", "people", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["api_slug"] == "people"

    def test_get_calls_client_with_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(cli, ["objects", "get", "obj_abc123", "--json"])
        mock_client.get_object.assert_called_once_with("obj_abc123")


# ── Objects create ────────────────────────────────────────────────────────

class TestObjectsCreate:
    def test_create_passes_slug_and_nouns(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "objects", "create",
                "--slug", "custom_thing",
                "--singular", "Thing",
                "--plural", "Things",
                "--json",
            ])
        assert result.exit_code == 0, result.output
        mock_client.create_object.assert_called_once_with(
            api_slug="custom_thing", singular_noun="Thing", plural_noun="Things"
        )

    def test_create_missing_slug_fails(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "objects", "create",
                "--singular", "Thing",
                "--plural", "Things",
            ])
        assert result.exit_code != 0


# ── Objects update ────────────────────────────────────────────────────────

class TestObjectsUpdate:
    def test_update_passes_data(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        data_json = json.dumps({"singular_noun": "NewThing"})
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "objects", "update", "obj_abc123",
                "--data", data_json,
                "--json",
            ])
        assert result.exit_code == 0, result.output
        mock_client.update_object.assert_called_once_with(
            "obj_abc123", {"singular_noun": "NewThing"}
        )

    def test_update_invalid_json_fails(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "objects", "update", "obj_abc123",
                "--data", "not-json",
            ])
        assert result.exit_code != 0


# ── Objects views ─────────────────────────────────────────────────────────

class TestObjectsViews:
    def test_views_returns_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["objects", "views", "people", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data

    def test_views_calls_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(cli, ["objects", "views", "people", "--json"])
        mock_client.list_object_views.assert_called_once_with("people")


# ── No delete command ─────────────────────────────────────────────────────

class TestObjectsNoDelete:
    def test_delete_command_does_not_exist(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["objects", "delete", "obj_abc123"])
        # Should exit with usage error (2) — no such command
        assert result.exit_code == 2
