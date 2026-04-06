"""Tests for formatter.py — JSON mode, TTY detection, stderr routing."""
import json
import sys
from io import StringIO

import pytest

# Add agent-harness to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from cli_anything.attio.utils.formatter import (
    format_error,
    format_output,
    format_pagination_footer,
)


SAMPLE_RECORD = {
    "id": {"record_id": "rec_test123"},
    "values": {
        "name": [{"value": "Test Person", "attribute_type": "text"}],
        "email_addresses": [{"email_address": "test@example.com", "attribute_type": "email"}],
    },
}


class TestJsonOutput:
    def test_json_flag_forces_json(self, capsys):
        format_output(SAMPLE_RECORD, as_json=True)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["id"]["record_id"] == "rec_test123"
        assert captured.err == ""

    def test_piped_output_is_json(self, capsys, monkeypatch):
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        format_output(SAMPLE_RECORD, as_json=False)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "id" in data

    def test_json_list_output(self, capsys):
        format_output([SAMPLE_RECORD], as_json=True)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 1


class TestErrorOutput:
    def test_error_goes_to_stderr(self, capsys):
        format_error("something went wrong")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "something went wrong" in captured.err

    def test_error_hint_appears_in_stderr(self, capsys):
        format_error("auth failed", hint="run: attio config set api-key")
        captured = capsys.readouterr()
        assert "Hint:" in captured.err
        assert "attio config set api-key" in captured.err
        assert captured.out == ""


class TestPaginationFooter:
    def test_footer_shown_in_terminal_mode(self, capsys, monkeypatch):
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        format_pagination_footer(25, has_more=True, as_json=False)
        captured = capsys.readouterr()
        assert "showing 25" in captured.out
        assert "--all" in captured.out

    def test_footer_json_mode_suppressed(self, capsys):
        """JSON mode suppresses footer to avoid breaking jq pipes."""
        format_pagination_footer(25, has_more=True, as_json=True)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_no_footer_when_no_more(self, capsys, monkeypatch):
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        format_pagination_footer(10, has_more=False, as_json=False)
        captured = capsys.readouterr()
        # No footer when has_more is False
        assert captured.out == ""
