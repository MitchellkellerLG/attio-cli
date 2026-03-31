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

SAMPLE_LIST = {
    "id": {"list_id": "list_abc123"},
    "name": "Sales Pipeline",
    "parent_object": "companies",
    "created_at": "2026-03-30T12:00:00.000Z",
}

SAMPLE_ENTRY = {
    "id": {"entry_id": "entry_abc123", "list_id": "list_abc123"},
    "parent_record_id": "rec_abc123",
    "values": {"status": [{"value": "Active"}]},
}

SAMPLE_LIST_VIEW = {
    "id": {"view_id": "view_abc123"},
    "name": "Default View",
}

SAMPLE_OBJECT = {
    "id": {"object_id": "obj_abc123"},
    "api_slug": "people",
    "singular_noun": "Person",
    "plural_noun": "People",
}

SAMPLE_ATTRIBUTE = {
    "id": {"attribute_id": "attr_abc123"},
    "title": "Email",
    "api_slug": "email_addresses",
    "type": "email",
}

SAMPLE_SELECT_OPTION = {
    "id": {"option_id": "opt_abc123"},
    "title": "High Priority",
}

SAMPLE_STATUS = {
    "id": {"status_id": "stat_abc123"},
    "title": "Active",
}

SAMPLE_VIEW = {
    "id": {"view_id": "view_abc123"},
    "name": "Default View",
}

SAMPLE_FILE = {
    "id": {"file_id": "file_abc123"},
    "name": "proposal.pdf",
    "size": 102400,
    "record_id": "rec_abc123",
    "object": "people",
    "created_at": "2026-03-30T12:00:00.000Z",
}

SAMPLE_MEETING = {
    "id": {"meeting_id": "meet_abc123"},
    "title": "Q4 Planning",
    "start_time": "2026-03-30T14:00:00.000Z",
    "end_time": "2026-03-30T15:00:00.000Z",
}

SAMPLE_RECORDING = {
    "id": {"recording_id": "rec_vid_abc123"},
    "meeting_id": "meet_abc123",
    "duration": 3600,
}

SAMPLE_TRANSCRIPT = {
    "data": [
        {"speaker": "Jane Smith", "text": "Let's discuss Q4 goals", "timestamp": 0.0},
    ]
}

SAMPLE_WEBHOOK = {
    "id": {"webhook_id": "whk_abc123"},
    "target_url": "https://example.com/webhook",
    "status": "active",
    "subscriptions": [{"event_type": "record.created"}],
    "created_at": "2026-03-30T12:00:00.000Z",
}

SAMPLE_WORKSPACE_MEMBER = {
    "id": {"workspace_member_id": "wm_abc123"},
    "name": "Mitch Keller",
    "email_address": "mitch@leadgrow.ai",
    "role": "owner",
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
    # Comments
    client.create_comment.return_value = SAMPLE_COMMENT
    client.get_comment.return_value = SAMPLE_COMMENT
    client.delete_comment.return_value = {}
    client.resolve_comment.return_value = SAMPLE_COMMENT
    client.unresolve_comment.return_value = SAMPLE_COMMENT
    # Threads
    client.list_threads.return_value = SAMPLE_THREADS_LIST_RESPONSE
    client.get_thread.return_value = SAMPLE_THREAD
    # Lists
    client.list_lists.return_value = {"data": [SAMPLE_LIST]}
    client.get_list.return_value = SAMPLE_LIST
    client.create_list.return_value = SAMPLE_LIST
    client.update_list.return_value = SAMPLE_LIST
    client.list_list_views.return_value = {"data": [SAMPLE_LIST_VIEW]}
    # Entries
    client.list_entries.return_value = iter([SAMPLE_ENTRY])
    client.get_entry.return_value = SAMPLE_ENTRY
    client.create_entry.return_value = SAMPLE_ENTRY
    client.update_entry.return_value = SAMPLE_ENTRY
    client.delete_entry.return_value = {}
    client.assert_entry.return_value = SAMPLE_ENTRY
    # Objects
    client.list_objects.return_value = {"data": [SAMPLE_OBJECT]}
    client.get_object.return_value = SAMPLE_OBJECT
    client.create_object.return_value = SAMPLE_OBJECT
    client.update_object.return_value = SAMPLE_OBJECT
    client.list_object_views.return_value = {"data": [SAMPLE_VIEW]}
    # Attributes
    client.list_attributes.return_value = {"data": [SAMPLE_ATTRIBUTE]}
    client.get_attribute.return_value = SAMPLE_ATTRIBUTE
    client.create_attribute.return_value = SAMPLE_ATTRIBUTE
    client.update_attribute.return_value = SAMPLE_ATTRIBUTE
    client.archive_attribute.return_value = {}
    client.list_attribute_options.return_value = {"data": [SAMPLE_SELECT_OPTION]}
    client.create_attribute_option.return_value = SAMPLE_SELECT_OPTION
    client.list_attribute_statuses.return_value = {"data": [SAMPLE_STATUS]}
    client.create_attribute_status.return_value = SAMPLE_STATUS
    # Files
    client.upload_file.return_value = SAMPLE_FILE
    client.get_file_info.return_value = SAMPLE_FILE
    client.list_files.return_value = {"data": [SAMPLE_FILE]}
    client.download_file.return_value = b"fake file content"
    client.delete_file.return_value = {}
    client.create_folder.return_value = {"data": {"folder_id": "fold_abc123"}}
    # Meetings
    client.list_meetings.return_value = {"data": [SAMPLE_MEETING]}
    client.get_meeting.return_value = SAMPLE_MEETING
    client.list_meeting_recordings.return_value = {"data": [SAMPLE_RECORDING]}
    client.get_meeting_transcript.return_value = SAMPLE_TRANSCRIPT
    # Webhooks
    client.create_webhook.return_value = SAMPLE_WEBHOOK
    client.get_webhook.return_value = SAMPLE_WEBHOOK
    client.list_webhooks.return_value = {"data": [SAMPLE_WEBHOOK]}
    client.update_webhook.return_value = SAMPLE_WEBHOOK
    client.delete_webhook.return_value = {}
    # Workspace
    client.list_workspace_members.return_value = {"data": [SAMPLE_WORKSPACE_MEMBER]}
    client.get_workspace_member.return_value = SAMPLE_WORKSPACE_MEMBER
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
