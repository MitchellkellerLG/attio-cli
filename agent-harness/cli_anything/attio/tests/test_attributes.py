"""Click CliRunner tests for the attributes command group."""
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


# ── Attributes list ───────────────────────────────────────────────────────

class TestAttributesList:
    def test_list_by_object_slug(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["attributes", "list", "--object", "people", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        mock_client.list_attributes.assert_called_once_with("people", target_type="objects")

    def test_list_by_list_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        """When --list is used, target_type must be 'lists'."""
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["attributes", "list", "--list", "list_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_attributes.assert_called_once_with("list_abc123", target_type="lists")

    def test_list_no_scope_fails(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["attributes", "list", "--json"])
        assert result.exit_code != 0


# ── Attributes get ────────────────────────────────────────────────────────

class TestAttributesGet:
    def test_get_by_slugs(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["attributes", "get", "people", "email_addresses", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["api_slug"] == "email_addresses"

    def test_get_calls_client_with_slugs(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            runner.invoke(cli, ["attributes", "get", "people", "email_addresses", "--json"])
        mock_client.get_attribute.assert_called_once_with("people", "email_addresses")


# ── Attributes create ─────────────────────────────────────────────────────

class TestAttributesCreate:
    def test_create_passes_all_options(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "create",
                "--object", "people",
                "--title", "Phone Number",
                "--slug", "phone_number",
                "--type", "text",
                "--json",
            ])
        assert result.exit_code == 0, result.output
        mock_client.create_attribute.assert_called_once_with(
            object_slug="people",
            title="Phone Number",
            api_slug="phone_number",
            type="text",
        )

    def test_create_missing_required_fails(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "create",
                "--object", "people",
                "--title", "Phone Number",
                # missing --slug and --type
            ])
        assert result.exit_code != 0


# ── Attributes update ─────────────────────────────────────────────────────

class TestAttributesUpdate:
    def test_update_passes_data(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        data_json = json.dumps({"title": "New Title"})
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "update", "people", "email_addresses",
                "--data", data_json,
                "--json",
            ])
        assert result.exit_code == 0, result.output
        mock_client.update_attribute.assert_called_once_with(
            "people", "email_addresses", {"title": "New Title"}
        )

    def test_update_invalid_json_fails(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "update", "people", "email_addresses",
                "--data", "not-valid-json",
            ])
        assert result.exit_code != 0


# ── Attributes archive ────────────────────────────────────────────────────

class TestAttributesArchive:
    def test_archive_calls_archive_not_delete(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        """Critical: archive command calls archive_attribute, never delete_attribute."""
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "archive", "people", "email_addresses",
                "--yes", "--json",
            ])
        assert result.exit_code == 0, result.output
        mock_client.archive_attribute.assert_called_once_with("people", "email_addresses")
        # Ensure delete was not called
        mock_client.delete_record.assert_not_called()

    def test_archive_without_yes_prompts(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["attributes", "archive", "people", "email_addresses"],
                input="n\n",
            )
        assert result.exit_code != 0
        mock_client.archive_attribute.assert_not_called()

    def test_archive_yes_flag_skips_confirmation(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "archive", "people", "email_addresses", "--yes",
            ])
        assert result.exit_code == 0, result.output
        mock_client.archive_attribute.assert_called_once()


# ── Attributes no delete ──────────────────────────────────────────────────

class TestAttributesNoDelete:
    def test_delete_command_does_not_exist(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["attributes", "delete", "people", "email_addresses"])
        # Should exit with usage error (2) — no such command
        assert result.exit_code == 2


# ── Attributes options ────────────────────────────────────────────────────

class TestAttributesOptions:
    def test_options_lists_select_options(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "options", "people", "priority", "--json"
            ])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        mock_client.list_attribute_options.assert_called_once_with("people", "priority")

    def test_options_create_passes_title(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "options-create", "people", "priority",
                "--title", "High Priority",
                "--json",
            ])
        assert result.exit_code == 0, result.output
        mock_client.create_attribute_option.assert_called_once_with(
            "people", "priority", "High Priority"
        )


# ── Attributes statuses ───────────────────────────────────────────────────

class TestAttributesStatuses:
    def test_statuses_lists_status_values(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "statuses", "deals", "stage", "--json"
            ])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        mock_client.list_attribute_statuses.assert_called_once_with("deals", "stage")

    def test_statuses_create_passes_title(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, [
                "attributes", "statuses-create", "deals", "stage",
                "--title", "Active",
                "--json",
            ])
        assert result.exit_code == 0, result.output
        mock_client.create_attribute_status.assert_called_once_with(
            "deals", "stage", "Active"
        )
