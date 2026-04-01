"""Click CliRunner tests for record command groups."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli
from cli_anything.attio.utils.exceptions import AuthError, NotFoundError


SAMPLE_PERSON = {
    "id": {"record_id": "rec_abc123"},
    "values": {"name": [{"value": "Jane Smith", "attribute_type": "text"}]},
}


def make_ctx_with_client(mock_client: MagicMock) -> list:
    """Return [load_config patch, AttioClient patch] that inject mock_client.

    Patches names in attio_cli module namespace (where they're imported into),
    not the source modules — otherwise the already-imported names in attio_cli
    are not intercepted.
    """
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


# ── People list ───────────────────────────────────────────────────────────

class TestPeopleList:
    def test_people_list_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_records.return_value = iter([SAMPLE_PERSON])
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["people", "list", "--json"])
        assert result.exit_code == 0, result.output
        # Output contains multi-line JSON record followed by pagination footer.
        # Split on double-newline boundary or find the record JSON object.
        output = result.output.strip()
        # Find the first complete JSON object (ends before the footer line)
        # The record JSON and footer are newline-separated; parse the first object
        import io
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(output)
        assert data["id"]["record_id"] == "rec_abc123"

    def test_people_list_empty(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_records.return_value = iter([])
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["people", "list", "--json"])
        assert result.exit_code == 0


# ── People get ────────────────────────────────────────────────────────────

class TestPeopleGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get_record.return_value = SAMPLE_PERSON
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["people", "get", "rec_abc123", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["record_id"] == "rec_abc123"
        mock_client.get_record.assert_called_once_with("people", "rec_abc123")


# ── People create ─────────────────────────────────────────────────────────

class TestPeopleCreate:
    def test_create_passes_values(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.create_record.return_value = SAMPLE_PERSON
        mock_client.ensure_valid.return_value = None
        values = json.dumps({"name": [{"value": "Jane"}]})
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["people", "create", "--values", values, "--json"])
        assert result.exit_code == 0, result.output
        mock_client.create_record.assert_called_once_with(
            "people", {"name": [{"value": "Jane"}]}
        )


# ── People update ─────────────────────────────────────────────────────────

class TestPeopleUpdate:
    def test_update_default_is_patch(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.update_record.return_value = SAMPLE_PERSON
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "people", "update", "rec_abc123",
                    "--values", '{"name": [{"value": "New"}]}',
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.update_record.assert_called_once()
        _, kwargs = mock_client.update_record.call_args
        assert kwargs.get("overwrite", False) is False

    def test_update_overwrite_flag(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.update_record.return_value = SAMPLE_PERSON
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["people", "update", "rec_abc123", "--values", "{}", "--overwrite", "--json"],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.update_record.call_args
        assert kwargs.get("overwrite") is True


# ── People assert ─────────────────────────────────────────────────────────

class TestPeopleAssert:
    def test_assert_passes_matching_attribute(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.assert_record.return_value = SAMPLE_PERSON
        mock_client.ensure_valid.return_value = None
        values = json.dumps({"email_addresses": [{"email_address": "jane@example.com"}]})
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "people", "assert",
                    "--matching-attribute", "email_addresses",
                    "--values", values,
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.assert_record.assert_called_once()
        args, kwargs = mock_client.assert_record.call_args
        assert args[0] == "people"
        assert kwargs.get("matching_attribute") == "email_addresses" or args[2] == "email_addresses"


# ── People delete ─────────────────────────────────────────────────────────

class TestPeopleDelete:
    def test_delete_with_yes_flag(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.delete_record.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["people", "delete", "rec_abc123", "--yes", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.delete_record.assert_called_once_with("people", "rec_abc123")

    def test_delete_without_yes_aborts(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["people", "delete", "rec_abc123", "--json"], input="n\n"
            )
        assert result.exit_code != 0
        mock_client.delete_record.assert_not_called()


# ── People search ─────────────────────────────────────────────────────────

class TestPeopleSearch:
    def test_search_passes_query(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.search_records.return_value = {"data": []}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["people", "search", "Jane", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.search_records.assert_called_once()
        args, kwargs = mock_client.search_records.call_args
        # First arg is object_slugs list, second is query
        assert "people" in args[0]
        assert args[1] == "Jane" or kwargs.get("query") == "Jane"


# ── Exit codes ────────────────────────────────────────────────────────────

class TestExitCodes:
    def test_auth_error_exit_code_4(self, runner: CliRunner) -> None:
        with patch("cli_anything.attio.attio_cli.load_config", side_effect=AuthError()):
            result = runner.invoke(cli, ["people", "list"])
        assert result.exit_code == 4

    def test_not_found_exit_code_3(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_record.side_effect = NotFoundError("people/rec_missing")
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["people", "get", "rec_missing"])
        assert result.exit_code == 3


# ── Filter DSL ────────────────────────────────────────────────────────────

class TestFilter:
    def test_filter_key_value(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_records.return_value = iter([])
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["people", "list", "--filter", "name=Jane", "--json"]
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.list_records.call_args
        assert kwargs["filter"] == {"name": {"$eq": "Jane"}}

    def test_filter_inline_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_records.return_value = iter([])
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["people", "list", "--filter", '{"name": {"$eq": "Jane"}}', "--json"],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.list_records.call_args
        assert kwargs["filter"] == {"name": {"$eq": "Jane"}}


# ── Generic records group ─────────────────────────────────────────────────

class TestRecordsGroup:
    def test_records_list_with_slug(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.list_records.return_value = iter([SAMPLE_PERSON])
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["records", "list", "custom_object", "--json"]
            )
        assert result.exit_code == 0, result.output
        args, kwargs = mock_client.list_records.call_args
        object_slug_used = args[0] if args else kwargs.get("object_slug")
        assert object_slug_used == "custom_object"

    def test_records_get_with_slug(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_record.return_value = SAMPLE_PERSON
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["records", "get", "custom_object", "rec_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.get_record.assert_called_once_with("custom_object", "rec_abc123")
