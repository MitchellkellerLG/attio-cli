"""Click CliRunner tests for the files command group."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli
from cli_anything.attio.tests.conftest import SAMPLE_FILE


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


# ── Files upload ──────────────────────────────────────────────────────────

class TestFilesUpload:
    def test_upload_passes_file_path(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path: Path
    ) -> None:
        """upload_file is called with the correct file_path, record_id, and object_slug."""
        test_file = tmp_path / "proposal.pdf"
        test_file.write_bytes(b"pdf content")
        mock_client.upload_file.return_value = SAMPLE_FILE
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "files", "upload",
                    "--file", str(test_file),
                    "--record-id", "rec_abc123",
                    "--object", "people",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.upload_file.assert_called_once_with(
            str(test_file), "rec_abc123", "people"
        )

    def test_upload_json_output(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path: Path
    ) -> None:
        test_file = tmp_path / "doc.txt"
        test_file.write_bytes(b"hello")
        mock_client.upload_file.return_value = SAMPLE_FILE
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "files", "upload",
                    "--file", str(test_file),
                    "--record-id", "rec_abc123",
                    "--object", "people",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["id"]["file_id"] == "file_abc123"

    def test_upload_requires_file(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["files", "upload", "--record-id", "rec_abc123", "--object", "people"],
            )
        assert result.exit_code != 0


# ── Files get ─────────────────────────────────────────────────────────────

class TestFilesGet:
    def test_get_by_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get_file_info.return_value = SAMPLE_FILE
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["files", "get", "file_abc123", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_file_info.assert_called_once_with("file_abc123")
        data = json.loads(result.output.strip())
        assert data["id"]["file_id"] == "file_abc123"

    def test_get_uses_correct_id(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get_file_info.return_value = SAMPLE_FILE
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["files", "get", "file_xyz999", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.get_file_info.assert_called_once_with("file_xyz999")


# ── Files list ────────────────────────────────────────────────────────────

class TestFilesList:
    def test_list_all(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_files.return_value = {"data": [SAMPLE_FILE]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(cli, ["files", "list", "--json"])
        assert result.exit_code == 0, result.output
        mock_client.list_files.assert_called_once_with(record_id=None, object_slug=None)

    def test_list_with_record_filter(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_files.return_value = {"data": [SAMPLE_FILE]}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["files", "list", "--record-id", "rec_abc123", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.list_files.assert_called_once_with(
            record_id="rec_abc123", object_slug=None
        )

    def test_list_with_object_filter(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.list_files.return_value = {"data": []}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["files", "list", "--object", "people", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.list_files.assert_called_once_with(
            record_id=None, object_slug="people"
        )


# ── Files download ────────────────────────────────────────────────────────

class TestFilesDownload:
    def test_download_writes_to_output(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path: Path
    ) -> None:
        """download command writes bytes to --output path."""
        expected_bytes = b"fake file content"
        mock_client.download_file.return_value = expected_bytes
        mock_client.ensure_valid.return_value = None
        output_file = tmp_path / "downloaded.pdf"
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["files", "download", "file_abc123", "--output", str(output_file)],
            )
        assert result.exit_code == 0, result.output
        assert output_file.exists()
        assert output_file.read_bytes() == expected_bytes
        mock_client.download_file.assert_called_once_with("file_abc123")

    def test_download_confirmation_message(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path: Path
    ) -> None:
        mock_client.download_file.return_value = b"data"
        mock_client.ensure_valid.return_value = None
        output_file = tmp_path / "out.bin"
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                ["files", "download", "file_abc123", "--output", str(output_file)],
            )
        assert result.exit_code == 0, result.output
        assert "Downloaded" in result.output


# ── Files delete ──────────────────────────────────────────────────────────

class TestFilesDelete:
    def test_delete_with_yes(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete_file.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["files", "delete", "file_abc123", "--yes", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_file.assert_called_once_with("file_abc123")

    def test_delete_without_yes_prompts(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.delete_file.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["files", "delete", "file_abc123", "--json"], input="n\n"
            )
        assert result.exit_code != 0
        mock_client.delete_file.assert_not_called()

    def test_delete_confirms_and_calls(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.delete_file.return_value = {}
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli, ["files", "delete", "file_abc123", "--json"], input="y\n"
            )
        assert result.exit_code == 0, result.output
        mock_client.delete_file.assert_called_once_with("file_abc123")


# ── Files create-folder ───────────────────────────────────────────────────

class TestFilesCreateFolder:
    def test_create_folder_passes_params(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.create_folder.return_value = {
            "id": {"folder_id": "folder_abc123"}, "name": "docs"
        }
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "files", "create-folder",
                    "--name", "docs",
                    "--record-id", "rec_abc123",
                    "--object", "people",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_client.create_folder.assert_called_once_with("docs", "rec_abc123", "people")

    def test_create_folder_json_output(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        mock_client.create_folder.return_value = {
            "id": {"folder_id": "folder_abc123"}, "name": "contracts"
        }
        mock_client.ensure_valid.return_value = None
        patches = make_ctx_with_client(mock_client)
        with patches[0], patches[1]:
            result = runner.invoke(
                cli,
                [
                    "files", "create-folder",
                    "--name", "contracts",
                    "--record-id", "rec_abc123",
                    "--object", "companies",
                    "--json",
                ],
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["name"] == "contracts"
