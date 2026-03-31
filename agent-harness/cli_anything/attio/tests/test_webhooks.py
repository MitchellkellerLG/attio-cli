"""Click CliRunner tests for the webhooks command group (full CRUD)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli
from cli_anything.attio.tests.conftest import SAMPLE_WEBHOOK


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


# ── Webhooks create ───────────────────────────────────────────────────────

class TestWebhooksCreate:
    def test_create_calls_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.create_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        subs = json.dumps([{"event_type": "record.created"}])
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "webhooks", "create",
                    "--target-url", "https://example.com/webhook",
                    "--subscriptions", subs,
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_webhook.assert_called_once_with(
            "https://example.com/webhook",
            [{"event_type": "record.created"}],
        )

    def test_create_passes_target_url_and_subscriptions(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.create_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        subs = json.dumps([{"event_type": "record.created"}, {"event_type": "record.updated"}])
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "webhooks", "create",
                    "--target-url", "https://hooks.example.com/attio",
                    "--subscriptions", subs,
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        call_args = mock_client.create_webhook.call_args
        assert call_args[0][0] == "https://hooks.example.com/attio"
        assert len(call_args[0][1]) == 2

    def test_create_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.create_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        subs = json.dumps([{"event_type": "record.created"}])
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "webhooks", "create",
                    "--target-url", "https://example.com/webhook",
                    "--subscriptions", subs,
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["webhook_id"] == "whk_abc123"

    def test_create_invalid_subscriptions_json(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "webhooks", "create",
                    "--target-url", "https://example.com/webhook",
                    "--subscriptions", "not-valid-json",
                ],
            )
        assert result.exit_code != 0
        mock_client.create_webhook.assert_not_called()

    def test_create_requires_target_url(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "webhooks", "create",
                    "--subscriptions", '[{"event_type": "record.created"}]',
                ],
            )
        assert result.exit_code != 0


# ── Webhooks get ──────────────────────────────────────────────────────────

class TestWebhooksGet:
    def test_get_calls_client_with_id(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["webhooks", "get", "whk_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_webhook.assert_called_once_with("whk_abc123")

    def test_get_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["webhooks", "get", "whk_abc123", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["target_url"] == "https://example.com/webhook"
        assert data["status"] == "active"

    def test_get_uses_correct_id(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["webhooks", "get", "whk_xyz999", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_webhook.assert_called_once_with("whk_xyz999")


# ── Webhooks list ─────────────────────────────────────────────────────────

class TestWebhooksList:
    def test_list_calls_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_webhooks.return_value = {"data": [SAMPLE_WEBHOOK]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["webhooks", "list", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_webhooks.assert_called_once()

    def test_list_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_webhooks.return_value = {"data": [SAMPLE_WEBHOOK]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["webhooks", "list", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert data["data"][0]["id"]["webhook_id"] == "whk_abc123"

    def test_list_empty(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_webhooks.return_value = {"data": []}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["webhooks", "list", "--json"])
        assert result.exit_code == 0, result.output


# ── Webhooks update ───────────────────────────────────────────────────────

class TestWebhooksUpdate:
    def test_update_calls_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.update_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        data = json.dumps({"status": "paused"})
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["webhooks", "update", "whk_abc123", "--data", data, "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.update_webhook.assert_called_once_with("whk_abc123", {"status": "paused"})

    def test_update_passes_data(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.update_webhook.return_value = SAMPLE_WEBHOOK
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        new_url = "https://new-endpoint.example.com/attio"
        data = json.dumps({"target_url": new_url})
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["webhooks", "update", "whk_abc123", "--data", data, "--json"]
            )
        assert result.exit_code == 0, result.output
        call_args = mock_client.update_webhook.call_args
        assert call_args[0][1]["target_url"] == new_url

    def test_update_invalid_data_json(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["webhooks", "update", "whk_abc123", "--data", "bad-json"],
            )
        assert result.exit_code != 0
        mock_client.update_webhook.assert_not_called()

    def test_update_requires_data(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["webhooks", "update", "whk_abc123"])
        assert result.exit_code != 0


# ── Webhooks delete ───────────────────────────────────────────────────────

class TestWebhooksDelete:
    def test_delete_with_yes(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete_webhook.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["webhooks", "delete", "whk_abc123", "--yes", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_webhook.assert_called_once_with("whk_abc123")

    def test_delete_prompts_without_yes(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.delete_webhook.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            # Provide 'n' to abort
            result = runner.invoke(
                cli, ["webhooks", "delete", "whk_abc123"], input="n\n"
            )
        assert result.exit_code != 0
        mock_client.delete_webhook.assert_not_called()

    def test_delete_uses_correct_id(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.delete_webhook.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["webhooks", "delete", "whk_xyz999", "--yes", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_webhook.assert_called_once_with("whk_xyz999")

    def test_delete_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete_webhook.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["webhooks", "delete", "whk_abc123", "--yes", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data == {}
