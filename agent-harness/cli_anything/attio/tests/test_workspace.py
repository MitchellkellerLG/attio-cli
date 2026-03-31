"""Click CliRunner tests for the workspace command group (read-only)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli
from cli_anything.attio.tests.conftest import SAMPLE_SELF_RESPONSE, SAMPLE_WORKSPACE_MEMBER


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


# ── Workspace members ─────────────────────────────────────────────────────

class TestWorkspaceMembers:
    def test_list_members(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_workspace_members.return_value = {"data": [SAMPLE_WORKSPACE_MEMBER]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "members", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_workspace_members.assert_called_once()

    def test_list_members_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.list_workspace_members.return_value = {"data": [SAMPLE_WORKSPACE_MEMBER]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "members", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert data["data"][0]["name"] == "Mitch Keller"

    def test_list_members_empty(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_workspace_members.return_value = {"data": []}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "members", "--json"])
        assert result.exit_code == 0, result.output


# ── Workspace member (single) ─────────────────────────────────────────────

class TestWorkspaceMember:
    def test_get_member_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get_workspace_member.return_value = SAMPLE_WORKSPACE_MEMBER
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "member", "wm_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_workspace_member.assert_called_once_with("wm_abc123")

    def test_get_member_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_workspace_member.return_value = SAMPLE_WORKSPACE_MEMBER
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "member", "wm_abc123", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["workspace_member_id"] == "wm_abc123"
        assert data["role"] == "owner"

    def test_get_member_uses_correct_id(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_workspace_member.return_value = SAMPLE_WORKSPACE_MEMBER
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "member", "wm_xyz999", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_workspace_member.assert_called_once_with("wm_xyz999")


# ── Workspace self ────────────────────────────────────────────────────────

class TestWorkspaceSelf:
    def test_self_shows_workspace(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.self_check.return_value = SAMPLE_SELF_RESPONSE
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "self", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.self_check.assert_called_once()

    def test_self_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.self_check.return_value = SAMPLE_SELF_RESPONSE
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "self", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert data["data"]["name"] == "LeadGrow.ai"

    def test_self_reuses_self_check(self, runner: CliRunner, mock_client: MagicMock) -> None:
        """Verify workspace self command calls self_check (not a separate endpoint)."""
        mock_client.self_check.return_value = SAMPLE_SELF_RESPONSE
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["workspace", "self", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.self_check.assert_called_once()
        # Should NOT call any other method
        mock_client.list_workspace_members.assert_not_called()
        mock_client.get_workspace_member.assert_not_called()

    def test_no_write_commands_exist(self) -> None:
        """Verify workspace group has no create/update/delete commands."""
        from cli_anything.attio.workspace import workspace_group

        command_names = list(workspace_group.commands.keys())
        for forbidden in ("create", "update", "delete", "assert"):
            assert forbidden not in command_names, (
                f"Workspace should be read-only but found command: {forbidden}"
            )
        for expected in ("members", "member", "self"):
            assert expected in command_names, (
                f"Expected workspace command not found: {expected}"
            )
