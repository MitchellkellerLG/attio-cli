# Stress Test Results — 2026-04-02

## Test Suite

- **Tests run:** 254
- **Passed:** 249
- **Failed:** 0
- **Skipped:** 5 (E2E tests — `ATTIO_API_KEY` not set in pytest environment; they ran fine when the CLI was invoked directly with the key from `~/.config/attio/config.json`)
- **Warnings:** 8 (all from `click-repl` using deprecated `protected_args` — cosmetic, not functional)

All unit tests pass clean. No failures.

---

## CLI Live Tests

| Command | Result | Notes |
|---------|--------|-------|
| `workspace self --json` | PASS | Returns valid JWT token info and workspace metadata |
| `workspace members --json` | FAIL | `NotFoundError: /workspace-members` — wrong API URL |
| `workspace member <id> --json` | NOT TESTED | Blocked by `workspace members` being broken |
| `people list --limit 3 --json` | PASS | Returns 3 record objects + pagination footer |
| `people search "test" --json` | FAIL | `httpx.HTTPStatusError: 400 Bad Request` — API rejects payload |
| `companies search "test" --json` | FAIL | Same 400 error — affects all `search` subcommands |
| `records search people "test" --json` | FAIL | Same 400 error — same `search_records()` path |
| `tasks list --not-completed --json` | PASS | Returns `{"data": []}` (no tasks in workspace) |
| `tasks list --not-completed --limit 5 --json` | FAIL | `No such option: --limit` — tasks list has no `--limit` flag |
| `notes list --json` | PASS | Returns notes with full content |
| `notes list --limit 3 --json` | FAIL | `No such option: --limit` — notes list has no `--limit` flag |
| `lists list --json` | PASS | Returns lists correctly |
| `webhooks list --json` | PASS | Returns `{"data": []}` |
| `companies list --limit 2 --json` | PASS | Returns records + footer JSON |
| `deals list --limit 3 --json` | PASS | Returns records |
| `objects list --json` | PASS | Returns object types |
| `attio --help` | PASS | Clean output, all command groups listed |
| `people --help` | PASS | All subcommands listed |
| `tasks --help` | PASS | All subcommands listed |

---

## Bugs Found

### Bug 1 — CRITICAL: `workspace members` / `workspace member` — Wrong API endpoint URL
- **Command:** `attio workspace members --json`, `attio workspace member <id> --json`
- **Expected:** Returns workspace member list
- **Actual:** `Error: Not found: /workspace-members` (exit code 3)
- **Root cause:** `attio_client.py` calls `GET /workspace-members` but the actual Attio v2 API endpoint is `GET /workspace_members` (underscore, not hyphen). Confirmed via direct curl: `curl https://api.attio.com/v2/workspace_members` returns a valid 200 with member data.
- **Affected code:** `AttioClient.list_workspace_members()` and `get_workspace_member()` — both use `/workspace-members` path
- **Severity:** HIGH — the entire workspace members feature is broken

### Bug 2 — HIGH: All `search` subcommands crash with HTTP 400
- **Commands:** `attio people search <query>`, `attio companies search <query>`, `attio records search <object> <query>`
- **Expected:** Returns matching records as JSON
- **Actual:** `httpx.HTTPStatusError: Client error '400 Bad Request'`
- **Root cause:** The Attio v2 search API (`POST /objects/records/search`) requires a `request_as` field in the request body. The current client sends `{"query": query, "objects": object_slugs, "limit": N}` but the API rejects it because `request_as` is missing/invalid. All tested `request_as` values (string `"workspace-member"`, `"user"`, `"api"`, and object format) returned "Invalid input" — this needs the correct value from Attio's current API docs.
- **Affected code:** `AttioClient.search_records()` in `attio_client.py` line 144-149
- **Severity:** HIGH — search is completely broken for all object types
- **Note:** This is a live API contract bug, not a code logic bug. The `search_records` implementation in tests passes because it's mocked. The 400 error is not caught as an `AttioError` — it surfaces as a raw `httpx.HTTPStatusError`, which means the error handling is also broken here (exits with an unformatted stack trace instead of a clean error message).

### Bug 3 — MEDIUM: `tasks list` and `notes list` have no `--limit` or pagination options
- **Commands:** `attio tasks list --limit 5`, `attio notes list --limit 3`
- **Expected:** Limit results (based on README examples and user expectation)
- **Actual:** `No such option: --limit`
- **Root cause:** The `tasks_list` and `notes_list` commands use `client.list_tasks()` and `client.list_notes()` which delegate to `GET /tasks` and `GET /notes` — simple GET endpoints without the `offset_paginator`. Neither the client methods nor the CLI commands expose `--limit` or `--all`. If the API returns a large number of tasks/notes, there is no way to cap output or paginate.
- **Affected code:** `tasks.py` `tasks_list` command and `notes.py` `notes_list` command
- **Severity:** MEDIUM — functional but breaks documented examples and the E2E test passes `--limit 5` which would fail if run with a real key

### Bug 4 — MEDIUM: `format_pagination_footer` in JSON mode emits a second JSON object on stdout, breaking `jq` pipes
- **Command:** `attio companies list --limit 2 --json | jq '.'`
- **Expected:** Valid JSON array or newline-delimited JSON (NDJSON)
- **Actual:** Each record is emitted as a separate JSON object, then a footer `{"count": 2, "has_more": true}` is appended. Result is N+1 separate JSON objects concatenated without a separator. `jq '.'` works, but `jq '.[] | ...'` fails — and any parser expecting a single JSON value (e.g. `json.loads()`) will fail.
- **Root cause:** `format_output` emits each record with `json.dumps` + `click.echo`, then `format_pagination_footer` emits a separate JSON object. No envelope.
- **Affected code:** `formatter.py` `format_pagination_footer()` and the streaming loop in `records.py`
- **Severity:** MEDIUM — breaks standard shell pipeline patterns like `attio people list --json | jq '.[]'` or any script that calls `json.loads()` on the full output

### Bug 5 — LOW: E2E test `test_workspace_members_returns_list` has a wrong assertion
- **File:** `tests/test_e2e.py` line 42
- **Expected assertion:** `assert isinstance(data, list)`
- **Actual API response:** `{"data": [...]}`  — a dict, not a list
- **Impact:** The E2E test would fail if run with the correct endpoint. The test expects a bare JSON array but the API returns a dict with a `data` key.
- **Severity:** LOW — test is currently skipped because `ATTIO_API_KEY` isn't set in the pytest env, but it would fail if E2E tests were enabled against the live API.

### Bug 6 — LOW: README documents `--email` flag for `people search` that doesn't exist
- **README says:** `attio people search --email <email>`
- **Actual:** `people search` only accepts a positional `QUERY` argument and `--limit`. No `--email` flag.
- **Severity:** LOW — documentation inaccuracy

### Bug 7 — LOW: README documents `webhooks create --events` flag that doesn't exist
- **README says:** `attio webhooks create --target-url <url> --events <event,...>`
- **Actual:** The flag is `--subscriptions` (JSON array format), not `--events`
- **Severity:** LOW — documentation inaccuracy, but the actual flag name is completely different

### Bug 8 — LOW: README project structure describes `client.py` that doesn't exist
- **README says:** The project structure includes `client.py` — described as "HTTP client"
- **Actual:** The file is `utils/attio_client.py`. There is no `client.py` in the package root.
- **Severity:** LOW — stale documentation

### Bug 9 — LOW: Unhandled `httpx.HTTPStatusError` on search (error surfacing)
- **Related to Bug 2.** When the 400 status code is returned by the search API, `_request()` falls through to `resp.raise_for_status()` which raises a raw `httpx.HTTPStatusError`. This is not caught as an `AttioError`, so the CLI exits with a full Python traceback instead of a clean error message.
- **Root cause:** `_request()` only handles 401, 404, 429, 500-504. A 400 from a valid call falls through to `raise_for_status()`, which is not wrapped.
- **Affected code:** `attio_client.py` `_request()` method — no handler for 400/422 validation errors
- **Severity:** LOW (a consequence of Bug 2, but the error handling gap exists independently)

---

## README vs Implementation Gaps

| README Claim | Actual Implementation | Gap Type |
|---|---|---|
| `people search --email <email>` | No `--email` flag; positional query only | Missing flag |
| `webhooks create --events <event,...>` | Flag is `--subscriptions` (JSON array) | Wrong flag name |
| Project structure: `client.py` | File is `utils/attio_client.py` | Stale doc |
| `tasks list --not-completed --json \| jq '...'` | Implies JSON is pipeable; actually NDJSON + footer breaks most parsers | Design gap |
| `prompt-toolkit` listed as dep ("REPL coming in v2") | REPL IS implemented in `repl.py` | Doc lag (minor) |
| Exit code `1 error` in Flags section | Exit code 1 is specifically `TransientError` (5xx); 2 is Click usage error | Incomplete |

---

## Recommendations (Prioritized)

1. **Fix `workspace-members` endpoint URL** — change `/workspace-members` to `/workspace_members` in `attio_client.py` lines 592 and 596. One-line fix, blocks the whole workspace members feature.

2. **Fix `search` API payload** — identify the correct `request_as` value or payload structure from current Attio API docs. The endpoint is correct (`POST /objects/records/search`) but the body schema has drifted. All search commands are dead until this is resolved.

3. **Wrap 400/422 in `_request()`** — add a handler in `_request()` for 4xx codes that don't have specific handling. At minimum, catch `httpx.HTTPStatusError` and re-raise as `AttioError` with the response body. Prevents raw tracebacks from surfacing to users.

4. **Add `--limit` to `tasks list` and `notes list`** — the Attio API for GET /tasks and GET /notes supports limit via query params. Add `--limit` option to both commands and pass it through to the client methods.

5. **Fix E2E test assertion for workspace members** — `test_workspace_members_returns_list` should assert `isinstance(data, dict) and "data" in data` or parse `data["data"]` as the list.

6. **Fix pagination footer in JSON mode** — either wrap all records in a JSON array with a `has_more` field at the top level, or suppress the footer in JSON mode. Current behavior breaks `jq` array operations and any single-call JSON parser.

7. **Fix README docs** — remove `--email` from `people search`, fix `webhooks create` to show `--subscriptions` with correct format, fix project structure map to show `utils/attio_client.py`.
