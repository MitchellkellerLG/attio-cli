# Phase 1: Foundation + Records - Research

**Researched:** 2026-03-30
**Domain:** Python CLI (Click + httpx) wrapping Attio REST API v2 — Records CRUD, pagination, rate limiting, auth
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Per-object top-level groups. `attio people list`, `attio companies get <id>`, `attio deals create`. Each standard object is a Click group. Maps 1:1 to Attio's API taxonomy.
- **D-02:** Generic `attio records` group also available for custom objects: `attio records list <object-slug>`. Standard objects are aliases for convenience.
- **D-03:** Single `update` command per object. PATCH by default (appends multiselect values). `--overwrite` flag switches to PUT (replaces multiselect values).
- **D-04:** Assert command (`attio people assert`) uses `--matching-attribute <slug>` to specify the match key. Warn in help text about multiselect asymmetry (matching attribute = additive, payload attributes = replacement).
- **D-05:** Triple filter interface: `--filter key=value` for simple equality, `--filter-file path.json` for complex filters, and raw `--filter '{json}'` for inline JSON. `@path.json` prefix accepted as shorthand for file path.
- **D-06:** When filter JSON parsing fails, emit helpful error with shell-escaping example for the detected shell.
- **D-07:** XDG-compliant config at `~/.config/attio/config.json`. REPL history at `~/.config/attio/history`. Never write config to working directory.
- **D-08:** `ATTIO_API_KEY` env var always takes precedence over config file. Config file stores API key + base URL override.
- **D-09:** Validate API key on first command (not every command) via `GET /v2/self`. Cache validation result for session.
- **D-10:** Contextual errors with actionable hints. Auth errors suggest `attio config set api-key`. 404s suggest the relevant list command. Rate limits show retry countdown to stderr.
- **D-11:** Authorization header redacted from all error output. Never log raw request objects.
- **D-12:** Retry on 429 (exponential backoff + Retry-After + jitter) AND on 500/502/503/504 (transient server errors). Max 3 retries.
- **D-13:** TTY-aware defaults: Rich tables when stdout is a terminal, JSON when piped. `--json` flag forces JSON regardless.
- **D-14:** Streaming pagination for `--all` flag. Output records page-by-page, never buffer all pages. Progress indicator to stderr.
- **D-15:** When results are paginated and `--all` not used, show footer: "(showing N results — use --all to fetch all pages)". In JSON mode, include `"has_more": true`.

### Claude's Discretion

- Table column selection for Rich output (which fields to show by default per object type)
- Progress indicator style (spinner vs count vs dots)
- `attio config` subcommand design (set/get/list/path)
- Test fixture organization
- Module import structure within cli_anything/attio/

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | CLI loads API key from `ATTIO_API_KEY` env var with fallback to `~/.config/attio/config.json` | python-dotenv loads env; XDG config path documented |
| INFRA-02 | CLI validates API key on first command via `GET /v2/self` and surfaces clear error if invalid | Session-level cache pattern; `GET /v2/self` confirmed |
| INFRA-03 | All HTTP requests go through a single AttioClient with bearer token injection, connection pooling, and timeout | httpx.Client pattern with ctx.obj injection |
| INFRA-04 | Rate limit handling with exponential backoff on 429s, Retry-After header respect, and jitter | Retry-After is timestamp; tenacity wait_fixed + jitter pattern |
| INFRA-05 | Retries on transient server errors (500/502/503/504) with backoff | tenacity retry_if_exception_type on HTTPStatusError |
| INFRA-06 | Cursor-based pagination with `--limit N` and `--all` flags on every list command | Attio uses offset pagination for records query; cursor response structure confirmed |
| INFRA-07 | Streaming output for `--all` pagination (page-by-page, no full buffer) | Generator/yield pattern; click.echo per record |
| INFRA-08 | `--json` flag on every command outputs raw JSON to stdout | formatter.py with as_json branch |
| INFRA-09 | TTY-aware default output (Rich tables if terminal, JSON if piped) | sys.stdout.isatty() detection; locked D-13 |
| INFRA-10 | Errors to stderr, data to stdout (Unix convention) | click.echo(..., err=True) |
| INFRA-11 | Semantic exit codes: 0=success, 1=generic error, 2=usage error, 3=not found, 4=auth failure, 5=rate limited | sys.exit() or Click exception with exit_code param |
| INFRA-12 | `--help` on every command and subcommand with accurate descriptions | Click generates from docstrings; rich-click improves formatting |
| INFRA-13 | Shell completion for bash/zsh/fish via Click 8 built-in | Click 8 shell_completion module, no third-party needed |
| INFRA-14 | Authorization header redacted from all error output and logs | Sanitize request headers before any logging |
| REC-01 | User can create a record on any standard object via `attio <object> create` | POST /v2/objects/{object}/records |
| REC-02 | User can get a single record by ID via `attio <object> get <id>` | GET /v2/objects/{object}/records/{record_id} |
| REC-03 | User can list/query records with filter and sort via `attio <object> list` | POST /v2/objects/{object}/records/query |
| REC-04 | User can update a record via PATCH (append multiselect) via `attio <object> update <id>` | PATCH /v2/objects/{object}/records/{record_id} |
| REC-05 | User can overwrite a record via PUT (replace multiselect) via `attio <object> update <id> --overwrite` | PUT /v2/objects/{object}/records/{record_id} |
| REC-06 | User can delete a record via `attio <object> delete <id>` | DELETE /v2/objects/{object}/records/{record_id} |
| REC-07 | User can assert (create-or-update) a record via `attio <object> assert --matching-attribute <slug>` | PUT /v2/objects/{object}/records with matching_attribute query param |
| REC-08 | User can fuzzy search records via `attio <object> search <query>` | POST /v2/objects/records/search with objects filter |
| REC-09 | Simple filter shorthand `--filter key=value` for common cases | Client-side conversion to Attio filter DSL |
| REC-10 | File-based complex filters via `--filter-file filters.json` | Load JSON file, pass as filter body |

</phase_requirements>

---

## Summary

Phase 1 builds the full CLI stack from scratch and validates it end-to-end against Records. There are no existing Python files in the repo — this is a greenfield build inside the CLI-Anything framework. The pattern is: lay each architectural layer (config, client, formatter, entry point, command groups) once, then the remaining 10+ command groups in Phase 2 are repetition of the Records pattern.

The technology stack is fully locked with no contested decisions. Python 3.10+, Click 8.3.1, httpx 0.28.1, tenacity 9.1.4, Rich 14.3.3, python-dotenv 1.2.2. The CLI-Anything framework requires `cli_anything/attio/attio_cli.py` as the entry point and `setup.py` with a `console_scripts` entry point.

Three Phase 1 risks demand architectural attention before any Records commands ship: (1) the PATCH vs PUT multiselect distinction — already resolved by D-03 (PATCH default, `--overwrite` for PUT), (2) score-based rate limiting that aggregates across all workspace tokens requiring exponential backoff not just Retry-After sleep, and (3) `--all` pagination that must stream per-page to avoid OOM on large datasets.

**Primary recommendation:** Build layers bottom-up in strict order — `config.py` → `attio_client.py` (with pagination + retry) → `formatter.py` → `records.py` → `attio_cli.py` — with tests at each layer. Records validates the full stack before Phase 2 repeats the pattern.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.10+ | Runtime | CLI-Anything hard requirement. Structural pattern matching for response dispatch. |
| Click | 8.3.1 | CLI framework | CLI-Anything hard requirement. Declarative commands, built-in shell completion, CliRunner for tests. |
| httpx | 0.28.1 | HTTP client | Sync-first, connection pooling, composable transport layer for mocking in tests. Direct successor to requests. |
| tenacity | 9.1.4 | Retry / backoff | Handles 429 + Retry-After + exponential backoff + jitter cleanly. Decorates the `_request()` helper. |
| rich | 14.3.3 | Terminal output | Tables, progress, syntax-highlighted JSON. TTY mode only — bypassed entirely by `--json` flag. |
| python-dotenv | 1.2.2 | Env/config loading | Loads `ATTIO_API_KEY` from `.env`. 12-factor compliant. Simpler than pydantic-settings for single env var. |
| prompt-toolkit | 3.0.52 | REPL + interactive input | CLI-Anything hard requirement. Powers REPL mode, history, key bindings. |
| pytest | 7.0+ | Testing | CLI-Anything hard requirement. Use with click.testing.CliRunner. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rich-click | 1.9+ | Rich-formatted help text | Single import swap at entry point only: `import rich_click as click`. Styled `--help` output for free. |
| pytest-httpx | 0.35+ | Mock httpx in tests | All unit tests that invoke HTTP. `HTTPXMock` fixture eliminates real network calls. |
| pytest-cov | latest | Coverage reporting | Track coverage across unit and E2E suites. |
| ruff | latest | Linting + formatting | Replaces flake8 + isort + black. Run in pre-commit. |
| mypy | latest | Type checking | Enforce strict mode from day one. Click 8, httpx, rich are all typed. |
| uv | latest | Package management | 10-100x faster than pip. `uv venv` + `uv pip install`. No code changes needed. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx | requests | requests has no composable transport for mocking, no HTTP/2. httpx is the direct successor. |
| tenacity | hand-rolled retry loop | Hand-rolling misses jitter, Retry-After parsing edge cases, and exception filtering. |
| python-dotenv | pydantic-settings | pydantic-settings is right for web apps with complex config. Overkill for one env var. |
| rich-click | Click default help | rich-click costs nothing (single import swap) and makes `--help` professional. |
| Click 8 shell_completion | click-completion | click-completion is abandoned. Click 8 ships native bash/zsh/fish completion built-in. |

**Installation:**
```bash
# Runtime deps
uv pip install click>=8.3.1 httpx>=0.28.1 tenacity>=9.1.4 rich>=14.3.3 python-dotenv>=1.2.2 prompt-toolkit>=3.0.52 rich-click>=1.9

# Dev + test deps
uv pip install pytest>=7.0 pytest-httpx>=0.35 pytest-cov ruff mypy
```

---

## Architecture Patterns

### Recommended Project Structure

```
agent-harness/
├── setup.py                          # entry_points: cli-anything-attio
├── SKILL.md                          # AI-discoverable capability doc
├── ATTIO.md                          # Human-readable SOP
│
└── cli_anything/
    └── attio/
        ├── __init__.py
        ├── attio_cli.py              # Root Click group, ctx.obj wiring, group registration
        │
        ├── records.py                # people, companies, deals, users — all CRUD
        │
        └── utils/
            ├── __init__.py
            ├── config.py             # env var + XDG config file resolution
            ├── attio_client.py       # httpx wrapper — auth, rate limit, retry, pagination
            ├── formatter.py          # Rich tables + raw JSON output
            └── pagination.py         # cursor + offset iterator (used by client)
        │
        └── tests/
            ├── conftest.py           # fixtures: mock client, canned API responses
            ├── test_client.py        # auth headers, rate limit, pagination, retry
            ├── test_commands.py      # Click CliRunner: flag behavior, exit codes
            ├── test_formatter.py     # JSON output, table rendering, TTY detection
            └── test_e2e.py           # Live API calls against LeadGrow workspace
```

Phase 1 only builds `records.py` from the command groups. The remaining 10+ groups (`notes.py`, `lists.py`, etc.) are Phase 2 repetition.

### Pattern 1: Client Injected via Click Context

The `AttioClient` is instantiated once at the root `@click.group()` and injected into `ctx.obj`. Every subcommand retrieves it via `@click.pass_context`. This gives one auth setup, one connection pool, and automatic REPL session persistence.

```python
# attio_cli.py
@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    ctx.ensure_object(dict)
    config = load_config()
    ctx.obj["client"] = AttioClient(api_key=config.api_key)

# records.py — people group as concrete example
@people.command("list")
@click.option("--limit", default=500, help="Max records per page")
@click.option("--all", "all_pages", is_flag=True, help="Fetch all pages (streaming)")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON")
@click.option("--filter", "filter_expr", multiple=True, help="key=value or JSON")
@click.option("--filter-file", type=click.Path(exists=True), help="Path to filter JSON file")
@click.pass_context
def list_people(ctx, limit, all_pages, output_json, filter_expr, filter_file):
    client: AttioClient = ctx.obj["client"]
    filter_body = build_filter(filter_expr, filter_file)
    for record in client.list_records("people", limit=limit, all_pages=all_pages, filter=filter_body):
        format_output(record, output_json)
```

### Pattern 2: Thin Command Layer

Commands parse args and route to client. Zero HTTP logic, zero JSON serialization, zero formatting decisions. A command that grows beyond ~50 lines is doing too much.

```python
# WRONG — HTTP bleeding into command layer
@people.command("get")
def get_person(record_id):
    resp = httpx.get(f"https://api.attio.com/v2/objects/people/records/{record_id}",
                     headers={"Authorization": f"Bearer {os.environ['ATTIO_API_KEY']}"})
    print(json.dumps(resp.json(), indent=2))

# RIGHT — delegate entirely
@people.command("get")
@click.argument("record_id")
@click.option("--json", "output_json", is_flag=True)
@click.pass_context
def get_person(ctx, record_id, output_json):
    result = ctx.obj["client"].get_record("people", record_id)
    format_output(result, output_json)
```

### Pattern 3: AttioClient Owns All HTTP Concerns

```python
# utils/attio_client.py
import httpx
import tenacity
import time
from typing import Iterator

class AttioClient:
    BASE_URL = "https://api.attio.com/v2"

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        self._validated = False

    def ensure_valid(self) -> None:
        """Validate API key via GET /v2/self. Called once per session (D-09)."""
        if self._validated:
            return
        resp = self._client.get("/self")
        if resp.status_code == 401:
            raise AuthError("Invalid API key. Run: attio config set api-key")
        resp.raise_for_status()
        self._validated = True

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type((RateLimitError, TransientError)),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=60) + tenacity.wait_random(0, 1),
        stop=tenacity.stop_after_attempt(3),
    )
    def _request(self, method: str, path: str, **kwargs) -> dict:
        resp = self._client.request(method, path, **kwargs)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", 1.0))
            raise RateLimitError(retry_after)
        if resp.status_code in (500, 502, 503, 504):
            raise TransientError(resp.status_code)
        resp.raise_for_status()
        return resp.json()

    def list_records(
        self,
        object_slug: str,
        limit: int = 500,
        all_pages: bool = False,
        filter: dict | None = None,
        sorts: list | None = None,
    ) -> Iterator[dict]:
        """Yield records page-by-page. Never buffers all results."""
        offset = 0
        while True:
            body = {"limit": limit, "offset": offset}
            if filter:
                body["filter"] = filter
            if sorts:
                body["sorts"] = sorts
            resp = self._request("POST", f"/objects/{object_slug}/records/query", json=body)
            data = resp.get("data", [])
            yield from data
            if len(data) < limit:
                break  # Offset end detection: fewer results than limit = last page
            offset += limit
            if not all_pages:
                break
```

**Source:** Attio pagination docs confirm offset pagination for records query. End detection: `len(data) < limit`. Cursor pagination response structure uses `pagination.next_cursor`.

### Pattern 4: Streaming Pagination (INFRA-07 + D-14)

The `--all` flag must stream output per-record as pages arrive, never buffer. Satisfies D-14 and prevents OOM on large datasets (Pitfall 4).

```python
# records.py — streaming output pattern
@people.command("list")
@click.option("--all", "all_pages", is_flag=True)
@click.option("--json", "output_json", is_flag=True)
@click.pass_context
def list_people(ctx, all_pages, output_json, ...):
    client = ctx.obj["client"]
    count = 0
    for record in client.list_records("people", all_pages=all_pages, ...):
        format_output(record, output_json, stream=True)
        count += 1
    if not all_pages and not output_json:
        click.echo(f"(showing {count} results — use --all to fetch all pages)", err=False)
```

Progress indicator goes to stderr so it doesn't corrupt stdout JSON: `click.echo(f"Fetching... ({count})", err=True)`.

### Pattern 5: Formatter Receives Raw Data

```python
# utils/formatter.py
import json
import sys
from rich.console import Console
from rich.table import Table

_console = Console()
_stderr_console = Console(stderr=True)

def format_output(data: dict | list, as_json: bool, stream: bool = False) -> None:
    """Single entry point for all output. Commands never call json.dumps directly."""
    if as_json or not sys.stdout.isatty():
        click.echo(json.dumps(data, indent=2))
        return
    _render_table(data)

def format_error(message: str, hint: str | None = None) -> None:
    """All errors go to stderr with actionable hints."""
    _stderr_console.print(f"[red]Error:[/red] {message}")
    if hint:
        _stderr_console.print(f"[dim]Hint: {hint}[/dim]")
```

### Pattern 6: Filter Construction (D-05)

The triple filter interface converts user input to Attio's filter DSL before the API call:

```python
# utils/attio_client.py or a filter_builder.py helper
import json
import os

def build_filter(filter_exprs: tuple[str, ...], filter_file: str | None) -> dict | None:
    """Build Attio filter body from CLI inputs. Priority: --filter-file > --filter."""
    if filter_file:
        # Support @path.json shorthand
        path = filter_file.lstrip("@")
        with open(path) as f:
            return json.load(f)
    if not filter_exprs:
        return None
    conditions = {}
    for expr in filter_exprs:
        if expr.startswith("{"):
            # Raw JSON inline
            try:
                return json.loads(expr)
            except json.JSONDecodeError:
                _emit_filter_parse_error(expr)  # D-06: helpful shell-escaping hint
        elif "=" in expr:
            key, _, value = expr.partition("=")
            conditions[key] = {"$eq": value}
        else:
            _emit_filter_parse_error(expr)
    return conditions if conditions else None
```

### Pattern 7: Semantic Exit Codes (INFRA-11)

```python
# utils/exceptions.py
import click
import sys

class AttioError(click.ClickException):
    def __init__(self, message: str, exit_code: int = 1, hint: str | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.hint = hint

    def show(self):
        format_error(self.format_message(), self.hint)

class AuthError(AttioError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, exit_code=4, hint="Run: attio config set api-key")

class NotFoundError(AttioError):
    def __init__(self, resource: str):
        super().__init__(f"Not found: {resource}", exit_code=3)

class RateLimitError(AttioError):
    def __init__(self, retry_after: float = 1.0):
        super().__init__(f"Rate limited. Retry after {retry_after:.1f}s", exit_code=5)

class TransientError(AttioError):
    def __init__(self, status_code: int):
        super().__init__(f"Server error {status_code}", exit_code=1)
```

### Pattern 8: XDG Config (D-07, D-08)

```python
# utils/config.py
import os
import json
from pathlib import Path
from dataclasses import dataclass

CONFIG_DIR = Path.home() / ".config" / "attio"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history"

@dataclass
class AttioConfig:
    api_key: str
    base_url: str = "https://api.attio.com/v2"

def load_config() -> AttioConfig:
    """D-08: env var takes precedence over config file."""
    api_key = os.getenv("ATTIO_API_KEY")
    base_url = "https://api.attio.com/v2"

    if not api_key and CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
        api_key = data.get("api_key")
        base_url = data.get("base_url", base_url)

    if not api_key:
        raise AuthError("ATTIO_API_KEY not set. Run: attio config set api-key")

    return AttioConfig(api_key=api_key, base_url=base_url)

def save_config(api_key: str, base_url: str | None = None) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {"api_key": api_key}
    if base_url:
        data["base_url"] = base_url
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    CONFIG_FILE.chmod(0o600)  # Security: owner-read only
```

### Anti-Patterns to Avoid

- **HTTP in command files:** All httpx calls live exclusively in `attio_client.py`. Zero HTTP outside that file.
- **Module-level singleton client:** Never use a module-level `client = AttioClient(...)`. Use `ctx.obj["client"]` exclusively — the REPL depends on it.
- **json.dumps in commands:** Only `formatter.py` touches JSON serialization. Commands call `format_output()`.
- **Buffering `--all` pages:** `list_records()` must be a generator. Never `results = []; results.extend(page)` then return.
- **PUT as default update:** PATCH is default. `--overwrite` opts into PUT. Never make PUT the default.
- **Logging raw request objects:** Sanitize before logging — redact `Authorization` header (D-11, INFRA-14).
- **Retry only 429:** Retry `500/502/503/504` too (INFRA-05, D-12).

---

## Attio API — Confirmed Endpoint Reference

All endpoints verified against official Attio docs as of 2026-03-30.

### Base URL
`https://api.attio.com/v2`

### Authentication
`Authorization: Bearer <ATTIO_API_KEY>` header on all requests.

### Records Endpoints (Phase 1 scope)

| Operation | Method | Path | Notes |
|-----------|--------|------|-------|
| List/query records | POST | `/objects/{object}/records/query` | Filter + sort + offset pagination in body |
| Create record | POST | `/objects/{object}/records` | `{"data": {"values": {...}}}` |
| Get record | GET | `/objects/{object}/records/{record_id}` | record_id must be UUID |
| Update (append) | PATCH | `/objects/{object}/records/{record_id}` | Multiselect: prepends new values |
| Update (overwrite) | PUT | `/objects/{object}/records/{record_id}` | Multiselect: replaces ALL values (data loss risk) |
| Assert (upsert) | PUT | `/objects/{object}/records` | `?matching_attribute=<slug>` query param required |
| Delete record | DELETE | `/objects/{object}/records/{record_id}` | Returns `{}` on success |
| Search (fuzzy) | POST | `/objects/records/search` | `objects` array required; eventually consistent |

### Search Endpoint Details
```json
POST /v2/objects/records/search
{
  "query": "search string",
  "objects": ["people"],
  "limit": 25,
  "request_as": {"workspace_member": {"email": "user@example.com"}}
}
```
- `objects` array is required (minimum 1 slug or UUID)
- `limit` range: 1–25 (not the standard 500)
- Results are "eventually consistent" — not guaranteed up-to-date
- Returns `record_text`, `record_image`, `object_slug` per result

### Pagination (Records Query)
- Records query uses **offset-based** pagination (not cursor-based)
- Parameters: `limit` (default 500), `offset` (default 0) in request body
- End detection: `len(response["data"]) < limit` means last page
- Keep limit and filter consistent across pages

### Filter DSL
Filters go in the POST body under the `filter` key:
```json
{
  "filter": {
    "name": {"$eq": "Acme Corp"}
  },
  "sorts": [{"direction": "asc", "attribute": "name"}]
}
```
Logical operators: `$and`, `$or`, `$not`.
Comparison operators: `$eq`, `$in`, `$not_empty`, `$contains`, `$starts_with`, `$ends_with`, `$lt`, `$lte`, `$gt`, `$gte`.
Note: `$` operators are shell variable expansion in bash/zsh — always use `--filter-file` for complex filters in shell scripts.

### Standard Object Slugs
`people`, `companies`, `deals`, `users`, `workspaces`

### Rate Limits
- Read: 100 requests/second
- Write: 25 requests/second
- Score-based: aggregates across ALL apps and access tokens on the workspace (10-second sliding window)
- 429 response includes `Retry-After` header (timestamp, not duration — convert to sleep duration)
- Score-based 429s can recur immediately after Retry-After if query complexity remains high

### Required OAuth Scopes (read-only reference — API key auth covers all)
- `record_permission:read` for reads
- `record_permission:read-write` for writes
- `object_configuration:read` for all operations

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP retry logic | Custom retry loop with try/except | tenacity with `@retry` decorator | Handles Retry-After parsing, jitter, max attempts, exception filtering. Edge cases in hand-rolled loops: missing jitter (thundering herd), wrong exception types caught. |
| Terminal output formatting | `print()` + ANSI codes | Rich `Table`, `Console` | Color stripping when not TTY, proper column wrapping, consistent field widths. Hand-rolled ANSI leaks into piped output. |
| Shell completion | Custom completer | Click 8 `shell_completion` module | Click generates bash/zsh/fish scripts from the command tree. Nothing to implement. |
| Help text formatting | Docstrings + manual | rich-click (single import swap) | Rich-click produces grouped, styled `--help` output with zero API changes. |
| REPL loop | prompt-toolkit PromptSession from scratch | click-repl | click-repl wires Click's command tree into prompt-toolkit. Avoids 200+ lines of dispatch code. (Phase 3 — not Phase 1.) |
| Env var loading | `os.environ.get()` + manual `.env` parsing | python-dotenv `load_dotenv()` | Handles `.env` file format edge cases, multi-line values, comments. One call replaces 20 lines. |

**Key insight:** The tenacity decorator on `_request()` is invisible to all other code. No retry complexity bleeds into command files or the client's public methods.

---

## Common Pitfalls

### Pitfall 1: PUT Silently Destroys Multiselect Values
**What goes wrong:** Using PUT when PATCH is intended on multiselect attributes replaces all existing values. Returns 200 — no error. Data is gone.
**Why it happens:** Both verbs map to "update record" mentally. The distinction is easy to miss.
**How to avoid:** D-03 resolves this by design — PATCH is default, `--overwrite` opts into PUT. The `AttioClient` must expose separate methods: `update_record()` for PATCH, `overwrite_record()` for PUT. Never a single method with a flag.
**Warning signs:** Users reporting disappearing tags or statuses after updates.

### Pitfall 2: Assert Multiselect Asymmetry
**What goes wrong:** The matching attribute in assert gets additive behavior (new values added, old values preserved). ALL OTHER multiselect attributes in the same payload get replacement behavior (values deleted to match supplied list).
**Why it happens:** Documented exception that's easy to miss.
**How to avoid:** `--help` for `assert` command must explicitly warn about this. Add integration test: assert a record with multiple multiselect attributes and verify the asymmetry.

### Pitfall 3: Score-Based 429s Are Not Request-Count 429s
**What goes wrong:** Exponential backoff waits and retries. Query hits score limit again immediately. Infinite retry loop on complex queries.
**Why it happens:** Score budget aggregates across all workspace tokens (Zapier, native integrations, other CLIs). CLI can hit score limit without having sent many requests.
**How to avoid:** Exponential backoff with jitter (not just Retry-After). Warn user: "Rate limit hit — workspace-shared budget may be constrained by other integrations." Consider inter-page delay when `--all` is fetching from a large object.

### Pitfall 4: `--all` OOM on Large Objects
**What goes wrong:** `--all` buffers all pages before output. 80k companies = 160 pages × ~500 records × object payload = potential OOM.
**Why it happens:** The natural `results.extend(page)` pattern works fine in tests against small datasets.
**How to avoid:** `list_records()` must be a Python generator (`yield from data`). Commands iterate and emit per-record. Never accumulate.

### Pitfall 5: Filter JSON Shell Quoting
**What goes wrong:** `attio people list --filter '{"$or": [...]}' ` fails in bash because `$or` triggers variable expansion. PowerShell quoting is entirely different.
**Why it happens:** Attio's filter operators all start with `$`, which is shell metachar.
**How to avoid:** `--filter-file` is the primary interface for complex filters. `--filter key=value` shorthand handles the simple equality case without JSON. When inline JSON fails, D-06 requires a helpful error with shell-escaping examples.

### Pitfall 6: ANSI Codes in `--json` Output
**What goes wrong:** Rich writes ANSI escape sequences to stdout. When `--json` is active, downstream `jq` or Python JSON parsing fails on the escape sequences.
**Why it happens:** Rich auto-detects TTY but the CLI may have Rich active at the wrong layer.
**How to avoid:** When `as_json=True` or `not sys.stdout.isatty()`, use `click.echo(json.dumps(...))` exclusively. Rich console must never write to stdout in non-TTY or `--json` mode.

### Pitfall 7: Record ID vs Slug Confusion
**What goes wrong:** User passes a slug where a UUID is expected. API returns 404 with no indication of the format mismatch.
**Why it happens:** Standard objects have slugs (`people`) but individual records only have UUIDs.
**How to avoid:** Validate that `record_id` arguments look like UUIDs before making the API call. If a non-UUID is passed, emit: "Record ID must be a UUID. Use `attio people list` to find IDs."

### Pitfall 8: Search Endpoint Quirks
**What goes wrong:** Search returns stale results; search doesn't work without `objects` array; search has limit cap of 25.
**Why it happens:** `/v2/objects/records/search` is eventually consistent (not real-time), requires `objects` filter, and has 1–25 limit.
**How to avoid:** Document "eventually consistent" in `--help`. Require `--object` flag (default to all standard objects). Cap `--limit` at 25 and document it.

---

## Code Examples

### setup.py Entry Point

```python
# agent-harness/setup.py
from setuptools import setup, find_packages

setup(
    name="cli-anything-attio",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.3.1",
        "httpx>=0.28.1",
        "tenacity>=9.1.4",
        "rich>=14.3.3",
        "python-dotenv>=1.2.2",
        "prompt-toolkit>=3.0.52",
        "rich-click>=1.9",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-attio=cli_anything.attio.attio_cli:main",
        ],
    },
)
```

### Root CLI Entry Point

```python
# cli_anything/attio/attio_cli.py
import rich_click as click
from cli_anything.attio.utils.config import load_config
from cli_anything.attio.utils.attio_client import AttioClient
from cli_anything.attio.records import people, companies, deals

@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Attio CRM CLI — full API access from the command line."""
    ctx.ensure_object(dict)
    config = load_config()
    client = AttioClient(api_key=config.api_key, base_url=config.base_url)
    client.ensure_valid()  # D-09: validate once per session
    ctx.obj["client"] = client

cli.add_command(people)
cli.add_command(companies)
cli.add_command(deals)

def main() -> None:
    cli()
```

### People Command Group (abbreviated)

```python
# cli_anything/attio/records.py
import rich_click as click
from cli_anything.attio.utils.formatter import format_output, format_record_list
from cli_anything.attio.utils.filter_builder import build_filter

@click.group("people")
def people():
    """Commands for People records."""

@people.command("list")
@click.option("--limit", default=500, show_default=True, help="Records per page")
@click.option("--all", "all_pages", is_flag=True, help="Fetch all pages (streaming output)")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON")
@click.option("--filter", "filter_exprs", multiple=True, metavar="KEY=VALUE|JSON|@FILE", help="Filter expression")
@click.option("--filter-file", type=click.Path(exists=True), help="Path to filter JSON file")
@click.option("--sort", "sort_attr", help="Attribute slug to sort by")
@click.option("--direction", default="asc", type=click.Choice(["asc", "desc"]), help="Sort direction")
@click.pass_context
def list_people(ctx, limit, all_pages, output_json, filter_exprs, filter_file, sort_attr, direction):
    """List people records with optional filtering and sorting."""
    client = ctx.obj["client"]
    filter_body = build_filter(filter_exprs, filter_file)
    sorts = [{"direction": direction, "attribute": sort_attr}] if sort_attr else None

    count = 0
    for record in client.list_records("people", limit=limit, all_pages=all_pages,
                                       filter=filter_body, sorts=sorts):
        format_output(record, output_json, stream=True)
        count += 1

    if not all_pages and not output_json:
        click.echo(f"(showing {count} results — use --all to fetch all pages)")
    elif not all_pages and output_json:
        # D-15: has_more signal in JSON mode handled per-page or as wrapper
        pass
```

### tenacity Retry Pattern

```python
# utils/attio_client.py
import tenacity

@tenacity.retry(
    retry=tenacity.retry_if_exception_type((RateLimitError, TransientServerError)),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=60) + tenacity.wait_random(0, 1),
    stop=tenacity.stop_after_attempt(3),
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
)
def _request(self, method: str, path: str, **kwargs) -> dict:
    resp = self._client.request(method, path, **kwargs)
    if resp.status_code == 429:
        retry_after = float(resp.headers.get("Retry-After", 1.0))
        click.echo(f"Rate limited. Retrying after {retry_after:.1f}s...", err=True)  # D-10
        raise RateLimitError(retry_after)
    if resp.status_code in (500, 502, 503, 504):
        raise TransientServerError(resp.status_code)
    resp.raise_for_status()
    return resp.json()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `requests` for HTTP clients | `httpx` (sync-first, composable transport) | 2022–2024 | Direct successor with identical sync API; better test ergonomics |
| Hand-rolled retry loops | `tenacity` with decorators | 2018+ | Retry logic is invisible to calling code |
| `click-completion` (third-party) | Click 8 built-in `shell_completion` | Click 8.0 (2021) | click-completion is abandoned; use Click built-in |
| Offset pagination as default | Cursor pagination preferred | Attio v2 | Attio uses offset for records query, cursor for list entries |
| `setup.py` only | `pyproject.toml` preferred | PEP 517/518 (2018+) | Either works for CLI-Anything; `setup.py` is what the framework generates |

**Deprecated/outdated:**
- `click-completion`: Abandoned. Never use. Click 8 built-in handles bash/zsh/fish.
- `requests` library: Not wrong, but httpx is the correct choice for new Python projects needing testable HTTP.
- `PyYAML` for config: JSON or `.env` is sufficient. YAML parser complexity unwarranted for a single API key.

---

## Open Questions

1. **Retry-After header format**
   - What we know: Attio docs say "Retry-After header containing the reset timestamp"
   - What's unclear: Is it a Unix timestamp (seconds since epoch) or a duration in seconds? The standard HTTP Retry-After can be either format.
   - Recommendation: Implement both: try parsing as float (duration); if > current time, treat as Unix timestamp and subtract `time.time()`. Test against a real 429 in the E2E suite.

2. **pytest-httpx 0.35+ compatibility with httpx 0.28.1**
   - What we know: Flagged in STATE.md as a blocker concern.
   - What's unclear: Exact compatibility matrix between pytest-httpx versions and httpx versions.
   - Recommendation: Verify on first test run. If incompatible, pin pytest-httpx to a version that matches httpx 0.28.x. The pytest-httpx changelog documents httpx version compatibility.

3. **Search `request_as` field**
   - What we know: POST /v2/objects/records/search requires `request_as` — either workspace-level or a specific workspace member (by ID or email).
   - What's unclear: What's the correct value for CLI use (non-interactive, no specific member context)?
   - Recommendation: Default to workspace-level context. Provide `--as-member-email` option for users who need member-scoped search. Test with LeadGrow workspace to confirm default behavior.

4. **Table column defaults for Rich output**
   - What we know: Marked Claude's Discretion in D-13.
   - What's unclear: Which Attio attributes exist on people vs companies vs deals in the LeadGrow workspace specifically.
   - Recommendation: For people: `name`, `email_addresses`, `company`. For companies: `name`, `domains`, `created_at`. For deals: `name`, `status`, `value`. Make these configurable or dynamically inferred from response keys.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Check with `python --version` or `py --version` | 3.10+ required | — |
| uv | Package mgmt | Check with `uv --version` | latest | `pip` |
| ATTIO_API_KEY | Auth | Set in `Everything_CC/.env` per CONTEXT.md | confirmed | — |
| Attio API | All commands | Live | v2 | — |
| pytest-httpx | Unit tests | To be installed | 0.35+ | — |

**Confirmed from CONTEXT.md:** "API key confirmed working: ATTIO_API_KEY in Everything_CC/.env, full read-write scopes, workspace LeadGrow.ai"

---

## Project Constraints (from CLAUDE.md)

These directives are enforced by the project's `CLAUDE.md` and must be honored in every plan and implementation task:

- **Tech stack locked:** Python 3.10+, Click, prompt-toolkit, pytest. No deviation.
- **API version:** v2 only. Never use v1.
- **Auth method:** API key only (no OAuth).
- **Output format:** Every command must support `--json` for agent consumption.
- **Testing:** Unit tests + E2E tests required. CLI-Anything standard.
- **Directory structure:** Must follow CLI-Anything conventions (`agent-harness/`, `cli_anything/attio/`, etc.).
- **Entry point:** `setup.py` with `entry_points` for `cli-anything-attio` console script.
- **GSD workflow:** All file changes go through GSD commands. No direct repo edits outside GSD.
- **Runtime:** Workspace runs on Bun for JS tools. Python tools use standard venv / uv.
- **Archive safety:** Never use `rm`. Move to archive with date prefix if deletion is needed.

---

## Sources

### Primary (HIGH confidence)
- Attio API Docs — Rate Limiting: https://docs.attio.com/rest-api/guides/rate-limiting
- Attio API Docs — Pagination: https://docs.attio.com/rest-api/guides/pagination
- Attio API Docs — Filtering and Sorting: https://docs.attio.com/rest-api/guides/filtering-and-sorting
- Attio API Docs — List Records (POST /records/query): https://docs.attio.com/rest-api/endpoint-reference/records/list-records
- Attio API Docs — Create Record: https://docs.attio.com/rest-api/endpoint-reference/records/create-a-record
- Attio API Docs — Get Record: https://docs.attio.com/rest-api/endpoint-reference/records/get-a-record
- Attio API Docs — PATCH Update: https://docs.attio.com/rest-api/endpoint-reference/records/update-a-record-append-multiselect-values
- Attio API Docs — PUT Overwrite: https://docs.attio.com/rest-api/endpoint-reference/records/update-a-record-overwrite-multiselect-values
- Attio API Docs — Assert: https://docs.attio.com/rest-api/endpoint-reference/records/assert-a-record
- Attio API Docs — Delete: https://docs.attio.com/rest-api/endpoint-reference/records/delete-a-record
- Attio API Docs — Search: https://docs.attio.com/rest-api/endpoint-reference/records/search-records
- CLI-Anything QUICKSTART: https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/QUICKSTART.md
- .planning/research/STACK.md — verified library versions and rationale
- .planning/research/ARCHITECTURE.md — component boundaries and build order
- .planning/research/PITFALLS.md — critical Attio-specific gotchas
- .planning/research/FEATURES.md — feature prioritization and anti-features

### Secondary (MEDIUM confidence)
- Click 8 documentation: https://click.palletsprojects.com/en/stable/ — shell completion, context passing
- httpx documentation: https://www.python-httpx.org/advanced/clients/ — Client configuration
- tenacity documentation: https://tenacity.readthedocs.io/ — retry decorator patterns
- FroeMic/attio-cli: https://github.com/FroeMic/attio-cli — reference implementation (community project)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI as of prior research; no contested decisions
- Attio API endpoints: HIGH — verified against official Attio docs with direct WebFetch
- Architecture patterns: HIGH — CLI-Anything framework conventions confirmed; Click ctx.obj pattern is standard
- Rate limiting + pagination behavior: HIGH — verified against official Attio rate limiting and pagination guides
- Search endpoint quirks: HIGH — verified `objects` required, limit 1-25, eventually consistent

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable API; re-verify if Attio releases major version change)
