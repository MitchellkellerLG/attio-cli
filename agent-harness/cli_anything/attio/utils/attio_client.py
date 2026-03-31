"""HTTP client with auth, retry, and pagination. The ONLY file that imports httpx."""
from typing import Any, Iterator

import httpx
import tenacity

from .exceptions import AuthError, NotFoundError, RateLimitError, TransientError
from .pagination import offset_paginator


class AttioClient:
    """Wraps httpx.Client with Attio auth, retry, and all record operations.

    INFRA-03: Bearer token injected on every request.
    INFRA-14: Authorization header NEVER appears in any exception message.
    """

    BASE_URL = "https://api.attio.com/v2"

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        self._api_key = api_key
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        self._validated = False

    def ensure_valid(self) -> None:
        """D-09: validate once per session via GET /self. Cached after first call."""
        if self._validated:
            return
        resp = self._client.get("/self")
        if resp.status_code == 401:
            raise AuthError()
        resp.raise_for_status()
        self._validated = True

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type((RateLimitError, TransientError)),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=60)
              + tenacity.wait_random(0, 1),
        stop=tenacity.stop_after_attempt(3),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """All HTTP traffic goes through here. Raises typed exceptions — never raw httpx errors.

        INFRA-14: Authorization header value NEVER included in any exception message.
        """
        resp = self._client.request(method, path, **kwargs)

        if resp.status_code == 401:
            raise AuthError()
        if resp.status_code == 404:
            raise NotFoundError(path)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", "1.0"))
            raise RateLimitError(retry_after)
        if resp.status_code in (500, 502, 503, 504):
            raise TransientError(resp.status_code)

        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ── Records operations ─────────────────────────────────────────────────

    def get_record(self, object_slug: str, record_id: str) -> dict[str, Any]:
        """GET /objects/{object}/records/{id}"""
        return self._request("GET", f"/objects/{object_slug}/records/{record_id}")

    def list_records(
        self,
        object_slug: str,
        limit: int = 500,
        all_pages: bool = False,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Streaming generator — delegates to offset_paginator. Never buffers all pages."""
        base_body: dict[str, Any] = {}
        if filter:
            base_body["filter"] = filter
        if sorts:
            base_body["sorts"] = sorts

        return offset_paginator(
            request_fn=self._request,
            method="POST",
            path=f"/objects/{object_slug}/records/query",
            base_body=base_body,
            limit=limit,
            all_pages=all_pages,
        )

    def create_record(self, object_slug: str, values: dict[str, Any]) -> dict[str, Any]:
        """POST /objects/{object}/records"""
        return self._request(
            "POST",
            f"/objects/{object_slug}/records",
            json={"data": {"values": values}},
        )

    def update_record(
        self,
        object_slug: str,
        record_id: str,
        values: dict[str, Any],
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """D-03: PATCH by default (append multiselect), PUT with overwrite=True (replace)."""
        method = "PUT" if overwrite else "PATCH"
        return self._request(
            method,
            f"/objects/{object_slug}/records/{record_id}",
            json={"data": {"values": values}},
        )

    def assert_record(
        self,
        object_slug: str,
        values: dict[str, Any],
        matching_attribute: str,
    ) -> dict[str, Any]:
        """D-04: PUT /objects/{object}/records?matching_attribute={slug} — upsert by attribute."""
        return self._request(
            "PUT",
            f"/objects/{object_slug}/records",
            params={"matching_attribute": matching_attribute},
            json={"data": {"values": values}},
        )

    def delete_record(self, object_slug: str, record_id: str) -> dict[str, Any]:
        """DELETE /objects/{object}/records/{id}"""
        return self._request("DELETE", f"/objects/{object_slug}/records/{record_id}")

    def search_records(
        self,
        object_slugs: list[str],
        query: str,
        limit: int = 25,
    ) -> dict[str, Any]:
        """POST /objects/records/search — limit range 1–25 (Attio cap)."""
        return self._request(
            "POST",
            "/objects/records/search",
            json={"query": query, "objects": object_slugs, "limit": min(limit, 25)},
        )

    def self_check(self) -> dict[str, Any]:
        """GET /self — used for auth validation and workspace info."""
        return self._request("GET", "/self")

    # ── Notes operations ──────────────────────────────────────────────────

    def create_note(
        self,
        parent_object: str,
        parent_record_id: str,
        title: str,
        content: str,
        format: str = "plaintext",
    ) -> dict[str, Any]:
        """POST /notes — create a note on a record."""
        return self._request(
            "POST",
            "/notes",
            json={
                "data": {
                    "parent_object": parent_object,
                    "parent_record_id": parent_record_id,
                    "title": title,
                    "content": content,
                    "format": format,
                }
            },
        )

    def get_note(self, note_id: str) -> dict[str, Any]:
        """GET /notes/{note_id}"""
        return self._request("GET", f"/notes/{note_id}")

    def list_notes(
        self,
        parent_object: str | None = None,
        parent_record_id: str | None = None,
    ) -> dict[str, Any]:
        """GET /notes — list notes with optional parent filters."""
        params: dict[str, Any] = {}
        if parent_object:
            params["parent_object"] = parent_object
        if parent_record_id:
            params["parent_record_id"] = parent_record_id
        return self._request("GET", "/notes", params=params)

    def update_note(
        self,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """PATCH /notes/{note_id}"""
        data: dict[str, Any] = {}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        return self._request("PATCH", f"/notes/{note_id}", json={"data": data})

    def delete_note(self, note_id: str) -> dict[str, Any]:
        """DELETE /notes/{note_id}"""
        return self._request("DELETE", f"/notes/{note_id}")

    # ── Tasks operations ──────────────────────────────────────────────────

    def create_task(
        self,
        content: str,
        deadline_at: str | None = None,
        is_completed: bool = False,
        assignees: list[dict[str, Any]] | None = None,
        linked_records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """POST /tasks — create a task."""
        data: dict[str, Any] = {"content": content, "is_completed": is_completed}
        if deadline_at:
            data["deadline_at"] = deadline_at
        if assignees:
            data["assignees"] = assignees
        if linked_records:
            data["linked_records"] = linked_records
        return self._request("POST", "/tasks", json={"data": data})

    def get_task(self, task_id: str) -> dict[str, Any]:
        """GET /tasks/{task_id}"""
        return self._request("GET", f"/tasks/{task_id}")

    def list_tasks(
        self,
        linked_object: str | None = None,
        linked_record_id: str | None = None,
        assignee: str | None = None,
        is_completed: bool | None = None,
    ) -> dict[str, Any]:
        """GET /tasks — list tasks with optional filters."""
        params: dict[str, Any] = {}
        if linked_object:
            params["linked_object"] = linked_object
        if linked_record_id:
            params["linked_record_id"] = linked_record_id
        if assignee:
            params["assignee"] = assignee
        if is_completed is not None:
            params["is_completed"] = str(is_completed).lower()
        return self._request("GET", "/tasks", params=params)

    def update_task(
        self,
        task_id: str,
        content: str | None = None,
        deadline_at: str | None = None,
        is_completed: bool | None = None,
        assignees: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """PATCH /tasks/{task_id}"""
        data: dict[str, Any] = {}
        if content is not None:
            data["content"] = content
        if deadline_at is not None:
            data["deadline_at"] = deadline_at
        if is_completed is not None:
            data["is_completed"] = is_completed
        if assignees is not None:
            data["assignees"] = assignees
        return self._request("PATCH", f"/tasks/{task_id}", json={"data": data})

    def delete_task(self, task_id: str) -> dict[str, Any]:
        """DELETE /tasks/{task_id}"""
        return self._request("DELETE", f"/tasks/{task_id}")
