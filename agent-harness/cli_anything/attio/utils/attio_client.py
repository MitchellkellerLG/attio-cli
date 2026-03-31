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
