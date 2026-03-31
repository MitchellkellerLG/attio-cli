"""Unit tests for AttioClient — auth, retry, pagination, record operations."""
import json
import sys
import os

import pytest
from pytest_httpx import HTTPXMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from cli_anything.attio.utils.attio_client import AttioClient
from cli_anything.attio.utils.exceptions import (
    AuthError,
    NotFoundError,
    RateLimitError,
    TransientError,
)

BASE = "https://api.attio.com/v2"
API_KEY = "test_api_key_123"

SAMPLE_PERSON = {
    "id": {"record_id": "rec_abc123"},
    "values": {"name": [{"value": "Jane Smith", "attribute_type": "text"}]},
}

SAMPLE_LIST_RESP = {"data": [SAMPLE_PERSON]}


@pytest.fixture
def client() -> AttioClient:
    return AttioClient(api_key=API_KEY)


class TestAuthHeader:
    def test_bearer_token_in_request(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/objects/people/records/rec_abc123",
            json=SAMPLE_PERSON,
        )
        client.get_record("people", "rec_abc123")
        request = httpx_mock.get_requests()[0]
        assert request.headers["Authorization"] == f"Bearer {API_KEY}"

    def test_auth_error_on_401(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=401, json={"error": "unauthorized"})
        with pytest.raises(AuthError) as exc_info:
            client.get_record("people", "rec_abc123")
        assert exc_info.value.exit_code == 4
        # D-11: API key must NOT appear in error message
        assert API_KEY not in str(exc_info.value)

    def test_auth_key_not_in_error_message(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=401, json={})
        with pytest.raises(AuthError) as exc_info:
            client._request("GET", "/self")
        assert "Bearer" not in exc_info.value.format_message()
        assert API_KEY not in exc_info.value.format_message()


class TestRetry:
    def test_429_raises_rate_limit_error(self, client: AttioClient, httpx_mock: HTTPXMock):
        # Add 3 429 responses to exhaust retries
        for _ in range(3):
            httpx_mock.add_response(
                status_code=429,
                headers={"Retry-After": "2.0"},
                json={},
            )
        with pytest.raises(RateLimitError) as exc_info:
            client.get_record("people", "rec_abc123")
        assert exc_info.value.exit_code == 5
        assert exc_info.value.retry_after == 2.0

    def test_503_raises_transient_error(self, client: AttioClient, httpx_mock: HTTPXMock):
        for _ in range(3):
            httpx_mock.add_response(status_code=503, json={})
        with pytest.raises(TransientError) as exc_info:
            client.get_record("people", "rec_abc123")
        assert exc_info.value.exit_code == 1

    def test_404_raises_not_found_no_retry(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=404, json={})
        with pytest.raises(NotFoundError) as exc_info:
            client.get_record("people", "nonexistent")
        assert exc_info.value.exit_code == 3
        # 404 is NOT retried — only 1 request made
        assert len(httpx_mock.get_requests()) == 1


class TestRecordOperations:
    def test_get_record(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/objects/people/records/rec_abc123",
            json=SAMPLE_PERSON,
        )
        result = client.get_record("people", "rec_abc123")
        assert result["id"]["record_id"] == "rec_abc123"

    def test_list_records_is_generator(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/objects/people/records/query",
            method="POST",
            json=SAMPLE_LIST_RESP,
        )
        result = client.list_records("people")
        import inspect
        assert inspect.isgenerator(result)
        records = list(result)
        assert len(records) == 1
        assert records[0]["id"]["record_id"] == "rec_abc123"

    def test_create_record_body(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/objects/people/records",
            json=SAMPLE_PERSON,
        )
        client.create_record("people", {"name": [{"value": "Jane"}]})
        req = httpx_mock.get_requests()[0]
        body = json.loads(req.content)
        assert "data" in body
        assert "values" in body["data"]

    def test_update_patch_default(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="PATCH",
            url=f"{BASE}/objects/people/records/rec_abc123",
            json=SAMPLE_PERSON,
        )
        client.update_record("people", "rec_abc123", {"name": [{"value": "New"}]})
        assert httpx_mock.get_requests()[0].method == "PATCH"

    def test_update_put_overwrite(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="PUT",
            url=f"{BASE}/objects/people/records/rec_abc123",
            json=SAMPLE_PERSON,
        )
        client.update_record("people", "rec_abc123", {}, overwrite=True)
        assert httpx_mock.get_requests()[0].method == "PUT"

    def test_assert_record_uses_matching_attribute(
        self, client: AttioClient, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{BASE}/objects/people/records?matching_attribute=email_addresses",
            json=SAMPLE_PERSON,
        )
        client.assert_record(
            "people",
            {"email_addresses": [{"email_address": "a@b.com"}]},
            "email_addresses",
        )
        req = httpx_mock.get_requests()[0]
        assert "matching_attribute=email_addresses" in str(req.url)

    def test_delete_record(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="DELETE",
            url=f"{BASE}/objects/people/records/rec_abc123",
            json={},
        )
        result = client.delete_record("people", "rec_abc123")
        assert result == {}

    def test_search_records_limit_capped(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/objects/records/search",
            json={"data": []},
        )
        client.search_records(["people"], "Jane", limit=100)
        req = httpx_mock.get_requests()[0]
        body = json.loads(req.content)
        # Limit must be capped at 25 (Attio search limit)
        assert body["limit"] <= 25


class TestEnsureValid:
    def test_ensure_valid_calls_self(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/self",
            json={"data": {"id": {"workspace_id": "ws1"}}},
        )
        client.ensure_valid()
        assert client._validated is True

    def test_ensure_valid_cached(self, client: AttioClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/self",
            json={"data": {}},
        )
        client.ensure_valid()
        client.ensure_valid()  # Second call — should NOT make another HTTP request
        assert len(httpx_mock.get_requests()) == 1
