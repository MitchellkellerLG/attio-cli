"""Shared pytest fixtures for the Attio CLI test suite."""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from unittest.mock import MagicMock, create_autospec
import pytest
from click.testing import CliRunner

from cli_anything.attio.utils.attio_client import AttioClient


# ── Canned API responses ───────────────────────────────────────────────────

SAMPLE_PERSON = {
    "id": {"record_id": "rec_abc123"},
    "values": {
        "name": [{"value": "Jane Smith", "attribute_type": "text"}],
        "email_addresses": [{"email_address": "jane@example.com", "attribute_type": "email"}],
    },
}

SAMPLE_COMPANY = {
    "id": {"record_id": "rec_def456"},
    "values": {
        "name": [{"value": "Acme Corp", "attribute_type": "text"}],
        "domains": [{"domain": "acme.com", "attribute_type": "domain"}],
    },
}

SAMPLE_RECORD_LIST_RESPONSE = {
    "data": [SAMPLE_PERSON],
    "pagination": {"offset": 0, "limit": 500, "has_more": False},
}

SAMPLE_SELF_RESPONSE = {
    "data": {
        "id": {"workspace_id": "ws_xyz"},
        "name": "LeadGrow.ai",
    }
}

SAMPLE_SEARCH_RESPONSE = {
    "data": [
        {
            "record_text": "Jane Smith",
            "record_image": None,
            "object_slug": "people",
            "record_id": "rec_abc123",
        }
    ]
}

SAMPLE_NOTE = {
    "id": {"note_id": "note_abc123"},
    "parent_object": "people",
    "parent_record_id": "rec_abc123",
    "title": "Meeting Notes",
    "content_plaintext": "Discussed Q4 goals",
    "created_at": "2026-03-30T12:00:00.000Z",
}

SAMPLE_TASK = {
    "id": {"task_id": "task_abc123"},
    "content": "Follow up with Jane",
    "is_completed": False,
    "deadline_at": "2026-04-15T00:00:00.000Z",
    "assignees": [],
    "linked_records": [{"target_object": "people", "target_record_id": "rec_abc123"}],
}


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def runner() -> CliRunner:
    """Click test runner — use mix_stderr=False to test stderr separately."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_client() -> MagicMock:
    """Pre-wired mock of AttioClient for command tests.

    Uses create_autospec so assert_record is recognized as a valid method
    (MagicMock() treats any attribute starting with 'assert' as a real
    assertion, which breaks setup when accessed directly).
    """
    client = create_autospec(AttioClient, instance=True)
    client.get_record.return_value = SAMPLE_PERSON
    client.list_records.return_value = iter([SAMPLE_PERSON])
    client.create_record.return_value = SAMPLE_PERSON
    client.update_record.return_value = SAMPLE_PERSON
    client.delete_record.return_value = {}
    client.assert_record.return_value = SAMPLE_PERSON
    client.search_records.return_value = SAMPLE_SEARCH_RESPONSE
    client.self_check.return_value = SAMPLE_SELF_RESPONSE
    # Notes
    client.create_note.return_value = SAMPLE_NOTE
    client.get_note.return_value = SAMPLE_NOTE
    client.list_notes.return_value = {"data": [SAMPLE_NOTE]}
    client.update_note.return_value = SAMPLE_NOTE
    client.delete_note.return_value = {}
    # Tasks
    client.create_task.return_value = SAMPLE_TASK
    client.get_task.return_value = SAMPLE_TASK
    client.list_tasks.return_value = {"data": [SAMPLE_TASK]}
    client.update_task.return_value = SAMPLE_TASK
    client.delete_task.return_value = {}
    return client


@pytest.fixture
def sample_person() -> dict:
    return SAMPLE_PERSON


@pytest.fixture
def sample_company() -> dict:
    return SAMPLE_COMPANY


@pytest.fixture
def sample_record_list() -> dict:
    return SAMPLE_RECORD_LIST_RESPONSE
