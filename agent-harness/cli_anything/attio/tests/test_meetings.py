"""Click CliRunner tests for the meetings command group (read-only)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli
from cli_anything.attio.tests.conftest import (
    SAMPLE_MEETING,
    SAMPLE_RECORDING,
    SAMPLE_TRANSCRIPT,
)


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


# ── Meetings list ─────────────────────────────────────────────────────────

class TestMeetingsList:
    def test_list_calls_client(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_meetings.return_value = {"data": [SAMPLE_MEETING]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["meetings", "list", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_meetings.assert_called_once()

    def test_list_json_output(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_meetings.return_value = {"data": [SAMPLE_MEETING]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["meetings", "list", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "data" in data
        assert data["data"][0]["title"] == "Q4 Planning"

    def test_list_empty(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_meetings.return_value = {"data": []}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["meetings", "list", "--json"])
        assert result.exit_code == 0, result.output


# ── Meetings get ──────────────────────────────────────────────────────────

class TestMeetingsGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get_meeting.return_value = SAMPLE_MEETING
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["meetings", "get", "meet_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_meeting.assert_called_once_with("meet_abc123")
        data = json.loads(result.output.strip())
        assert data["id"]["meeting_id"] == "meet_abc123"

    def test_get_uses_correct_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get_meeting.return_value = SAMPLE_MEETING
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["meetings", "get", "meet_xyz999", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_meeting.assert_called_once_with("meet_xyz999")


# ── Meetings recordings ───────────────────────────────────────────────────

class TestMeetingsRecordings:
    def test_recordings_calls_client(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.list_meeting_recordings.return_value = {"data": [SAMPLE_RECORDING]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["meetings", "recordings", "meet_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.list_meeting_recordings.assert_called_once_with("meet_abc123")

    def test_recordings_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.list_meeting_recordings.return_value = {"data": [SAMPLE_RECORDING]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["meetings", "recordings", "meet_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["data"][0]["id"]["recording_id"] == "rec_vid_abc123"


# ── Meetings transcript ───────────────────────────────────────────────────

class TestMeetingsTranscript:
    def test_transcript_calls_client(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_meeting_transcript.return_value = SAMPLE_TRANSCRIPT
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "meetings", "transcript",
                    "meet_abc123", "rec_vid_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.get_meeting_transcript.assert_called_once_with(
            "meet_abc123", "rec_vid_abc123"
        )

    def test_transcript_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.get_meeting_transcript.return_value = SAMPLE_TRANSCRIPT
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "meetings", "transcript",
                    "meet_abc123", "rec_vid_abc123",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["data"][0]["speaker"] == "Jane Smith"

    def test_no_write_commands_exist(self) -> None:
        """Verify meetings group has no create/update/delete commands."""
        from cli_anything.attio.meetings import meetings_group

        command_names = list(meetings_group.commands.keys())
        for forbidden in ("create", "update", "delete", "assert"):
            assert forbidden not in command_names, (
                f"Meetings should be read-only but found command: {forbidden}"
            )
        for expected in ("list", "get", "recordings", "transcript"):
            assert expected in command_names, (
                f"Expected meetings command not found: {expected}"
            )
