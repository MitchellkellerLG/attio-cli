"""Offset-based pagination iterator for Attio records query endpoint."""
from typing import Any, Callable, Iterator

import click


def offset_paginator(
    request_fn: Callable[..., dict[str, Any]],
    method: str,
    path: str,
    base_body: dict[str, Any],
    limit: int,
    all_pages: bool,
) -> Iterator[dict[str, Any]]:
    """Yield records one-by-one from Attio's offset-paginated query endpoint.

    Never buffers all results in memory — pure generator.

    Args:
        request_fn: AttioClient._request — handles auth, retry, backoff
        method: HTTP method (always "POST" for records query)
        path: API path (e.g. "/objects/people/records/query")
        base_body: Base request body (filter, sorts — NOT limit/offset)
        limit: Records per page (max 500)
        all_pages: If True, iterate all pages. If False, stop after first page.
    """
    offset = 0
    page_num = 0

    while True:
        page_num += 1
        body = {**base_body, "limit": limit, "offset": offset}
        resp = request_fn(method, path, json=body)
        data = resp.get("data", [])

        yield from data

        if all_pages and len(data) == limit:
            # More pages may exist — progress indicator to stderr
            offset += limit
            total_so_far = offset
            click.echo(
                f"Fetched page {page_num} ({total_so_far} records so far)...",
                err=True,
            )
        else:
            # Either not fetching all pages, or len(data) < limit means last page
            break
