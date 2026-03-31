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

SAMPLE_COMMENT = {
    "id": {"comment_id": "cmnt_abc123"},
    "thread_id": "thrd_abc123",
    "body": "Looks good to me",
    "created_at": "2026-03-30T12:00:00.000Z",
    "resolved_at": None,
}

SAMPLE_THREAD = {
    "id": {"thread_id": "thrd_abc123"},
    "record_id": "rec_abc123",
    "comments": [SAMPLE_COMMENT],
    "resolved_at": None,
}

SAMPLE_THREADS_LIST_RESPONSE = {
    "data": [SAMPLE_THREAD],
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
    # Comments
    client.create_comment.return_value = SAMPLE_COMMENT
    client.get_comment.return_value = SAMPLE_COMMENT
    client.delete_comment.return_value = {}
    client.resolve_comment.return_value = SAMPLE_COMMENT
    client.unresolve_comment.return_value = SAMPLE_COMMENT
    # Threads
    client.list_threads.return_value = SAMPLE_THREADS_LIST_RESPONSE
    client.get_thread.return_value = SAMPLE_THREAD
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
