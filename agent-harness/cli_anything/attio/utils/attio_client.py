"""HTTP client with auth, retry, and pagination. The ONLY file that imports httpx."""
from pathlib import Path
from typing import Any, Iterator

import httpx
import tenacity

from .exceptions import AttioError, AuthError, NotFoundError, RateLimitError, TransientError
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
        if resp.status_code in (400, 422):
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise AttioError(f"Bad request ({resp.status_code}): {body}")
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
            json={
                "query": query,
                "objects": object_slugs,
                "limit": min(limit, 25),
                "request_as": None,
            },
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
        limit: int | None = None,
    ) -> dict[str, Any]:
        """GET /notes — list notes with optional parent filters."""
        params: dict[str, Any] = {}
        if parent_object:
            params["parent_object"] = parent_object
        if parent_record_id:
            params["parent_record_id"] = parent_record_id
        if limit is not None:
            params["limit"] = limit
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
        limit: int | None = None,
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
        if limit is not None:
            params["limit"] = limit
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

    # ── Comments operations ────────────────────────────────────────────────

    def create_comment(
        self,
        body: str,
        record_id: str | None = None,
        entry_id: str | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /comments — create a comment. thread_id=None starts a new thread."""
        data: dict[str, Any] = {"body": body}
        if thread_id:
            data["thread_id"] = thread_id
        if record_id:
            data["record_id"] = record_id
        if entry_id:
            data["entry_id"] = entry_id
        return self._request("POST", "/comments", json={"data": data})

    def get_comment(self, comment_id: str) -> dict[str, Any]:
        """GET /comments/{comment_id}"""
        return self._request("GET", f"/comments/{comment_id}")

    def delete_comment(self, comment_id: str) -> dict[str, Any]:
        """DELETE /comments/{comment_id}"""
        return self._request("DELETE", f"/comments/{comment_id}")

    def resolve_comment(self, comment_id: str) -> dict[str, Any]:
        """POST /comments/{comment_id}/resolve — mark thread resolved."""
        return self._request("POST", f"/comments/{comment_id}/resolve")

    def unresolve_comment(self, comment_id: str) -> dict[str, Any]:
        """POST /comments/{comment_id}/unresolve — mark thread unresolved."""
        return self._request("POST", f"/comments/{comment_id}/unresolve")

    # ── Threads operations ─────────────────────────────────────────────────

    def list_threads(
        self,
        record_id: str | None = None,
        entry_id: str | None = None,
    ) -> dict[str, Any]:
        """GET /threads — list threads on a record or entry."""
        params: dict[str, Any] = {}
        if record_id:
            params["record_id"] = record_id
        if entry_id:
            params["entry_id"] = entry_id
        return self._request("GET", "/threads", params=params)

    def get_thread(self, thread_id: str) -> dict[str, Any]:
        """GET /threads/{thread_id} — get thread with all comments."""
        return self._request("GET", f"/threads/{thread_id}")

    # ── Lists operations ───────────────────────────────────────────────────

    def list_lists(self) -> dict[str, Any]:
        """GET /lists — list all lists."""
        return self._request("GET", "/lists")

    def get_list(self, list_id: str) -> dict[str, Any]:
        """GET /lists/{list_id}"""
        return self._request("GET", f"/lists/{list_id}")

    def create_list(self, name: str, parent_object: str) -> dict[str, Any]:
        """POST /lists — create a list."""
        return self._request("POST", "/lists", json={"data": {"name": name, "parent_object": parent_object}})

    def update_list(self, list_id: str, name: str) -> dict[str, Any]:
        """PATCH /lists/{list_id} — update a list."""
        return self._request("PATCH", f"/lists/{list_id}", json={"data": {"name": name}})

    def list_list_views(self, list_id: str) -> dict[str, Any]:
        """GET /lists/{list_id}/views — list views for a list."""
        return self._request("GET", f"/lists/{list_id}/views")

    # ── List Entries operations ────────────────────────────────────────────

    def list_entries(
        self,
        list_id: str,
        limit: int = 500,
        all_pages: bool = False,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Streaming generator for list entries — delegates to offset_paginator."""
        base_body: dict[str, Any] = {}
        if filter:
            base_body["filter"] = filter
        if sorts:
            base_body["sorts"] = sorts
        return offset_paginator(
            request_fn=self._request,
            method="POST",
            path=f"/lists/{list_id}/entries/query",
            base_body=base_body,
            limit=limit,
            all_pages=all_pages,
        )

    def get_entry(self, list_id: str, entry_id: str) -> dict[str, Any]:
        """GET /lists/{list_id}/entries/{entry_id}"""
        return self._request("GET", f"/lists/{list_id}/entries/{entry_id}")

    def create_entry(
        self,
        list_id: str,
        parent_record_id: str,
        values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST /lists/{list_id}/entries — create a list entry."""
        data: dict[str, Any] = {"parent_record_id": parent_record_id}
        if values:
            data["values"] = values
        return self._request("POST", f"/lists/{list_id}/entries", json={"data": data})

    def update_entry(
        self,
        list_id: str,
        entry_id: str,
        values: dict[str, Any],
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """PATCH (default) or PUT (overwrite=True) /lists/{list_id}/entries/{entry_id}."""
        method = "PUT" if overwrite else "PATCH"
        return self._request(method, f"/lists/{list_id}/entries/{entry_id}", json={"data": {"values": values}})

    def delete_entry(self, list_id: str, entry_id: str) -> dict[str, Any]:
        """DELETE /lists/{list_id}/entries/{entry_id}"""
        return self._request("DELETE", f"/lists/{list_id}/entries/{entry_id}")

    def assert_entry(
        self,
        list_id: str,
        parent_record_id: str,
        values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """PUT /lists/{list_id}/entries — upsert entry by parent record."""
        data: dict[str, Any] = {"parent_record_id": parent_record_id}
        if values:
            data["values"] = values
        return self._request("PUT", f"/lists/{list_id}/entries", json={"data": data})

    # ── Objects operations ─────────────────────────────────────────────────

    def list_objects(self) -> dict[str, Any]:
        """GET /objects — list all object types."""
        return self._request("GET", "/objects")

    def get_object(self, object_id: str) -> dict[str, Any]:
        """GET /objects/{id} — get object by ID or slug."""
        return self._request("GET", f"/objects/{object_id}")

    def create_object(self, api_slug: str, singular_noun: str, plural_noun: str) -> dict[str, Any]:
        """POST /objects — create a custom object type."""
        return self._request(
            "POST",
            "/objects",
            json={"data": {"api_slug": api_slug, "singular_noun": singular_noun, "plural_noun": plural_noun}},
        )

    def update_object(self, object_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /objects/{id} — update object metadata."""
        return self._request("PATCH", f"/objects/{object_id}", json={"data": data})

    def list_object_views(self, object_id: str) -> dict[str, Any]:
        """GET /objects/{id}/views — list views for an object."""
        return self._request("GET", f"/objects/{object_id}/views")

    # ── Attributes operations ──────────────────────────────────────────────

    def list_attributes(self, target: str, target_type: str = "objects") -> dict[str, Any]:
        """GET /{target_type}/{target}/attributes — list attributes on object or list."""
        return self._request("GET", f"/{target_type}/{target}/attributes")

    def get_attribute(self, object_slug: str, attribute_slug: str) -> dict[str, Any]:
        """GET /objects/{object}/attributes/{attribute}"""
        return self._request("GET", f"/objects/{object_slug}/attributes/{attribute_slug}")

    def create_attribute(self, object_slug: str, title: str, api_slug: str, type: str) -> dict[str, Any]:
        """POST /objects/{object}/attributes — create attribute on an object."""
        return self._request(
            "POST",
            f"/objects/{object_slug}/attributes",
            json={"data": {"title": title, "api_slug": api_slug, "type": type}},
        )

    def update_attribute(self, object_slug: str, attribute_slug: str, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /objects/{object}/attributes/{attribute}"""
        return self._request(
            "PATCH",
            f"/objects/{object_slug}/attributes/{attribute_slug}",
            json={"data": data},
        )

    def archive_attribute(self, object_slug: str, attribute_slug: str) -> dict[str, Any]:
        """POST /objects/{object}/attributes/{attribute}/archive — ARCHIVE (not delete)."""
        return self._request(
            "POST",
            f"/objects/{object_slug}/attributes/{attribute_slug}/archive",
        )

    def list_attribute_options(self, object_slug: str, attribute_slug: str) -> dict[str, Any]:
        """GET /objects/{object}/attributes/{attribute}/options"""
        return self._request("GET", f"/objects/{object_slug}/attributes/{attribute_slug}/options")

    def create_attribute_option(self, object_slug: str, attribute_slug: str, title: str) -> dict[str, Any]:
        """POST /objects/{object}/attributes/{attribute}/options — add select option."""
        return self._request(
            "POST",
            f"/objects/{object_slug}/attributes/{attribute_slug}/options",
            json={"data": {"title": title}},
        )

    def list_attribute_statuses(self, object_slug: str, attribute_slug: str) -> dict[str, Any]:
        """GET /objects/{object}/attributes/{attribute}/statuses"""
        return self._request("GET", f"/objects/{object_slug}/attributes/{attribute_slug}/statuses")

    def create_attribute_status(self, object_slug: str, attribute_slug: str, title: str) -> dict[str, Any]:
        """POST /objects/{object}/attributes/{attribute}/statuses — add status value."""
        return self._request(
            "POST",
            f"/objects/{object_slug}/attributes/{attribute_slug}/statuses",
            json={"data": {"title": title}},
        )

    # ── Files operations ──────────────────────────────────────────────────

    def upload_file(self, file_path: str, record_id: str, object_slug: str) -> dict[str, Any]:
        """Upload binary file via multipart form. Does NOT use _request (different content type)."""
        with open(file_path, "rb") as f:
            resp = self._client.post(
                "/files/upload",
                files={"file": (Path(file_path).name, f)},
                data={"record_id": record_id, "object": object_slug},
            )
        if resp.status_code == 401:
            raise AuthError()
        if resp.status_code == 404:
            raise NotFoundError(f"record {record_id}")
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def get_file_info(self, file_id: str) -> dict[str, Any]:
        """GET /files/{file_id} — get file metadata."""
        return self._request("GET", f"/files/{file_id}")

    def list_files(
        self,
        record_id: str | None = None,
        object_slug: str | None = None,
    ) -> dict[str, Any]:
        """GET /files — list files, optionally filtered by record_id and/or object slug."""
        params: dict[str, Any] = {}
        if record_id:
            params["record_id"] = record_id
        if object_slug:
            params["object"] = object_slug
        return self._request("GET", "/files", params=params)

    def download_file(self, file_id: str) -> bytes:
        """Download file binary. Returns raw bytes (NOT JSON)."""
        resp = self._client.get(f"/files/{file_id}/download")
        if resp.status_code == 401:
            raise AuthError()
        if resp.status_code == 404:
            raise NotFoundError(f"file {file_id}")
        resp.raise_for_status()
        return resp.content

    def delete_file(self, file_id: str) -> dict[str, Any]:
        """DELETE /files/{file_id} — delete a file."""
        return self._request("DELETE", f"/files/{file_id}")

    def create_folder(
        self, name: str, record_id: str, object_slug: str
    ) -> dict[str, Any]:
        """POST /files/folders — create a folder on a record."""
        return self._request(
            "POST",
            "/files/folders",
            json={"data": {"name": name, "record_id": record_id, "object": object_slug}},
        )

    # ── Webhooks operations ───────────────────────────────────────────────

    def create_webhook(self, target_url: str, subscriptions: list[dict[str, Any]]) -> dict[str, Any]:
        """POST /webhooks — create a webhook subscription."""
        return self._request("POST", "/webhooks", json={"data": {"target_url": target_url, "subscriptions": subscriptions}})

    def get_webhook(self, webhook_id: str) -> dict[str, Any]:
        """GET /webhooks/{webhook_id}"""
        return self._request("GET", f"/webhooks/{webhook_id}")

    def list_webhooks(self) -> dict[str, Any]:
        """GET /webhooks — list all webhooks."""
        return self._request("GET", "/webhooks")

    def update_webhook(self, webhook_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /webhooks/{webhook_id} — update target_url, subscriptions, or status."""
        return self._request("PATCH", f"/webhooks/{webhook_id}", json={"data": data})

    def delete_webhook(self, webhook_id: str) -> dict[str, Any]:
        """DELETE /webhooks/{webhook_id}"""
        return self._request("DELETE", f"/webhooks/{webhook_id}")

    # ── Workspace operations ──────────────────────────────────────────────

    def list_workspace_members(self) -> dict[str, Any]:
        """GET /workspace_members — list all workspace members."""
        return self._request("GET", "/workspace_members")

    def get_workspace_member(self, member_id: str) -> dict[str, Any]:
        """GET /workspace_members/{member_id} — get a member by ID."""
        return self._request("GET", f"/workspace_members/{member_id}")

    # self_check() already exists — reused for workspace self command

    # ── Meetings operations (read-only) ───────────────────────────────────

    def list_meetings(self) -> dict[str, Any]:
        """GET /meetings — list all meetings."""
        return self._request("GET", "/meetings")

    def get_meeting(self, meeting_id: str) -> dict[str, Any]:
        """GET /meetings/{meeting_id} — get a meeting by ID."""
        return self._request("GET", f"/meetings/{meeting_id}")

    def list_meeting_recordings(self, meeting_id: str) -> dict[str, Any]:
        """GET /meetings/{meeting_id}/recordings — list recordings for a meeting."""
        return self._request("GET", f"/meetings/{meeting_id}/recordings")

    def get_meeting_transcript(
        self, meeting_id: str, recording_id: str
    ) -> dict[str, Any]:
        """GET /meetings/{meeting_id}/recordings/{recording_id}/transcript — get transcript."""
        return self._request(
            "GET", f"/meetings/{meeting_id}/recordings/{recording_id}/transcript"
        )
