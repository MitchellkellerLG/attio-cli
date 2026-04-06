"""Click CliRunner tests for the tasks command group."""
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


# ── Tasks create ──────────────────────────────────────────────────────────

class TestTasksCreate:
    def test_create_minimal(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["tasks", "create", "--content", "Follow up with Jane", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_task.assert_called_once_with(
            content="Follow up with Jane",
            deadline_at=None,
            assignees=None,
            linked_records=None,
        )

    def test_create_returns_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["tasks", "create", "--content", "Task", "--json"],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["task_id"] == "task_abc123"

    def test_create_with_deadline(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "tasks", "create",
                    "--content", "Task",
                    "--deadline", "2026-04-15T00:00:00.000Z",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.create_task.call_args
        assert kwargs["deadline_at"] == "2026-04-15T00:00:00.000Z"

    def test_create_with_assignee_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        assignee_json = '{"referenced_actor_type":"workspace-member","referenced_actor_id":"mem_123"}'
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "tasks", "create",
                    "--content", "Task",
                    "--assignee", assignee_json,
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.create_task.call_args
        assert kwargs["assignees"] == [
            {"referenced_actor_type": "workspace-member", "referenced_actor_id": "mem_123"}
        ]

    def test_create_missing_content(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["tasks", "create"])
        assert result.exit_code != 0


# ── Tasks get ─────────────────────────────────────────────────────────────

class TestTasksGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["tasks", "get", "task_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_task.assert_called_once_with("task_abc123")

    def test_get_returns_task_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["tasks", "get", "task_abc123", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["content"] == "Follow up with Jane"


# ── Tasks list ────────────────────────────────────────────────────────────

class TestTasksList:
    def test_list_no_filters(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["tasks", "list", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_tasks.assert_called_once_with(
            linked_object=None,
            linked_record_id=None,
            assignee=None,
            is_completed=None,
            limit=None,
        )

    def test_list_completed_flag(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["tasks", "list", "--completed", "--json"])
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.list_tasks.call_args
        assert kwargs["is_completed"] is True

    def test_list_not_completed_flag(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["tasks", "list", "--not-completed", "--json"])
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.list_tasks.call_args
        assert kwargs["is_completed"] is False

    def test_list_returns_valid_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["tasks", "list", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert len(data["data"]) == 1

    def test_list_with_linked_record_filter(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "tasks", "list",
                    "--linked-object", "people",
                    "--linked-record-id", "rec_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.list_tasks.assert_called_once_with(
            linked_object="people",
            linked_record_id="rec_abc123",
            assignee=None,
            is_completed=None,
            limit=None,
        )


# ── Tasks update ──────────────────────────────────────────────────────────

class TestTasksUpdate:
    def test_update_content(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["tasks", "update", "task_abc123", "--content", "New content", "--json"],
            )
        assert result.exit_code == 0, result.output
        mock_client.update_task.assert_called_once_with(
            "task_abc123",
            content="New content",
            deadline_at=None,
            is_completed=None,
        )

    def test_update_mark_completed(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["tasks", "update", "task_abc123", "--completed", "--json"],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.update_task.call_args
        assert kwargs["is_completed"] is True

    def test_update_mark_not_completed(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["tasks", "update", "task_abc123", "--not-completed", "--json"],
            )
        assert result.exit_code == 0, result.output
        _, kwargs = mock_client.update_task.call_args
        assert kwargs["is_completed"] is False

    def test_update_returns_task_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["tasks", "update", "task_abc123", "--content", "Updated", "--json"],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["task_id"] == "task_abc123"


# ── Tasks delete ──────────────────────────────────────────────────────────

class TestTasksDelete:
    def test_delete_with_yes_flag(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["tasks", "delete", "task_abc123", "--yes", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_task.assert_called_once_with("task_abc123")

    def test_delete_without_yes_aborts(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["tasks", "delete", "task_abc123", "--json"], input="n\n"
            )
        assert result.exit_code != 0
        mock_client.delete_task.assert_not_called()

    def test_delete_yes_skips_prompt(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["tasks", "delete", "task_abc123", "--yes"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_task.assert_called_once_with("task_abc123")
