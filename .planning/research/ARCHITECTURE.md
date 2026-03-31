# Architecture Research

**Domain:** API CLI wrapper (Attio CRM)
**Researched:** 2026-03-30
**Confidence:** HIGH

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INVOCATION                             │
│        attio <group> <command> [args] [--json] [--all]              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      ENTRY POINT LAYER                              │
│                    attio_cli.py (Click root)                        │
│  - Loads config (env var / config file)                             │
│  - Instantiates AttioClient, injects into Click context (ctx.obj)  │
│  - Registers all command groups                                     │
│  - Starts REPL if `attio repl` invoked                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      COMMAND LAYER                                  │
│         One file per resource group (records.py, lists.py...)      │
│  - Click @group / @command decorators                               │
│  - @pass_context to receive AttioClient from ctx.obj               │
│  - Validates user-supplied args (not API args — that's client)     │
│  - Calls client methods with typed arguments                       │
│  - Passes response to formatter                                     │
└─────────────┬───────────────────────────────────────────┬───────────┘
              │                                           │
┌─────────────▼──────────────┐           ┌───────────────▼───────────┐
│      API CLIENT LAYER      │           │    OUTPUT FORMATTER LAYER │
│      client.py             │           │      formatter.py         │
│                            │           │                           │
│  - httpx.Client wrapper   │           │  - --json → json.dumps    │
│  - Bearer token injection  │           │  - default → Rich table   │
│  - Rate limit tracking     │           │    or click.echo lines    │
│    (100r/s, 25w/s)        │           │  - Respects --quiet flag  │
│  - 429 + Retry-After wait │           │  - Consistent field order │
│  - Cursor pagination       │           │                           │
│  - Offset pagination       │           └───────────────────────────┘
│  - --limit / --all logic   │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│      CONFIG LAYER          │
│      config.py             │
│                            │
│  - Reads ATTIO_API_KEY env │
│  - Falls back to           │
│    ~/.attio/config.json    │
│  - Validates key presence  │
│  - Exposes workspace_id    │
└────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          REPL LAYER                                 │
│                    repl_skin.py (from harness)                      │
│  - prompt-toolkit PromptSession                                     │
│  - History file at ~/.attio/history                                │
│  - Tab completion from Click commands                               │
│  - ctx.obj (AttioClient) persisted across commands                 │
│  - Startup banner auto-reads SKILL.md                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | File(s) | Owns | Does NOT Own |
|-----------|---------|------|--------------|
| Entry point | `attio_cli.py` | App bootstrap, context wiring, group registration | HTTP, formatting, config reading |
| Command groups | `records.py`, `lists.py`, `notes.py`, etc. | CLI arguments, routing to client methods | HTTP mechanics, output rendering |
| API client | `utils/attio_client.py` | HTTP calls, auth headers, rate limiting, retry, pagination | CLI flags, output format decisions |
| Formatter | `utils/formatter.py` | Rendering API responses to terminal or JSON | Knows nothing about HTTP or Click state |
| Config | `utils/config.py` | Resolving API key + workspace config | HTTP, rendering, CLI |
| REPL | `utils/repl_skin.py` | Interactive session loop, history, completion | Business logic |
| Tests | `tests/` | Correctness verification | Production behavior |

---

## Recommended Project Structure

```
agent-harness/
├── setup.py                         # PEP 420 namespace pkg, entry_points
├── ATTIO.md                         # Human-readable SOP
├── SKILL.md                         # AI-discoverable capability doc
│
└── cli_anything/
    └── attio/
        ├── __init__.py
        ├── attio_cli.py             # Root Click group + repl command
        │
        ├── records.py               # people, companies, deals, users
        ├── lists.py                 # list management + views
        ├── list_entries.py          # entries within lists
        ├── attributes.py            # attributes + select options + statuses
        ├── custom_objects.py        # custom object definitions + views
        ├── notes.py
        ├── tasks.py
        ├── comments.py              # comments + threads
        ├── files.py                 # upload, download, folders
        ├── meetings.py              # meetings + recordings + transcripts
        ├── webhooks.py
        ├── workspace.py             # workspace members + /self validation
        │
        ├── utils/
        │   ├── __init__.py
        │   ├── attio_client.py      # httpx wrapper — single class, all HTTP
        │   ├── config.py            # env var + config file resolution
        │   ├── formatter.py         # Rich tables + JSON output
        │   ├── pagination.py        # cursor + offset iterator (used by client)
        │   └── repl_skin.py         # copy from harness, minimal modification
        │
        └── tests/
            ├── TEST.md
            ├── conftest.py          # fixtures: mock client, sample responses
            ├── test_client.py       # unit: auth headers, rate limit, pagination
            ├── test_commands.py     # unit: Click command parsing, flag behavior
            ├── test_formatter.py    # unit: JSON output, table rendering
            └── test_e2e.py          # E2E: real API calls against LeadGrow workspace
```

One file per resource group is the right granularity. Grouping all CRUD in a single file creates 2000+ line modules. One group per file keeps each file under ~300 lines and maps directly to Attio's API resource taxonomy.

---

## Architectural Patterns

### Pattern 1: Client as Context Object

Inject a single `AttioClient` instance into Click's context at the root group. Every subcommand retrieves it via `@click.pass_context`.

```python
# attio_cli.py
@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    config = load_config()
    ctx.obj["client"] = AttioClient(api_key=config.api_key)

# records.py
@records.command("get")
@click.argument("object_type")
@click.argument("record_id")
@click.option("--json", "output_json", is_flag=True)
@click.pass_context
def get_record(ctx, object_type, record_id, output_json):
    client = ctx.obj["client"]
    result = client.get(f"/objects/{object_type}/records/{record_id}")
    format_output(result, output_json)
```

This pattern means: one HTTP client, one auth header setup, one connection pool. The REPL inherits the same ctx.obj — context persists across interactive commands automatically.

**Confidence: HIGH** — standard Click pattern, confirmed in click-repl docs.

### Pattern 2: Thin Command Layer

Commands are argument parsers + routing only. No business logic, no HTTP. The command's job is: parse args, call client method, pass result to formatter.

```python
# WRONG — HTTP logic bleeding into command layer
@records.command("list")
@click.pass_context
def list_records(ctx, ...):
    resp = httpx.get(f"https://api.attio.com/v2/objects/{obj}/records", headers=...)
    # ...

# RIGHT — command delegates entirely
@records.command("list")
@click.pass_context
def list_records(ctx, obj, limit, all_pages, output_json):
    results = ctx.obj["client"].list_records(obj, limit=limit, all_pages=all_pages)
    format_output(results, output_json)
```

### Pattern 3: Client Encapsulates All HTTP Concerns

`AttioClient` owns everything HTTP-related. No other layer touches httpx.

```python
class AttioClient:
    def __init__(self, api_key: str, base_url: str = "https://api.attio.com/v2"):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        self._read_limiter = TokenBucket(rate=100, per=1.0)
        self._write_limiter = TokenBucket(rate=25, per=1.0)

    def get(self, path: str, params: dict = None) -> dict:
        self._read_limiter.consume()
        return self._request("GET", path, params=params)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        for attempt in range(3):
            resp = self._client.request(method, path, **kwargs)
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 1.0))
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        raise click.ClickException("Rate limit retries exhausted")
```

Use `httpx.Client` (not `requests`) — synchronous, supports type annotations, and is the direction the ecosystem is moving. The CLI-Anything framework doesn't prescribe a specific HTTP client, so httpx is the right call for a new project in 2025+.

**Confidence: HIGH** — httpx is the de-facto standard for new Python HTTP client work as of 2024-2025.

### Pattern 4: Pagination Iterator in Client Layer

Pagination should be completely invisible to command code. Commands pass `all_pages=True` or `limit=N` — the client handles cursor chaining.

```python
def paginate(self, path: str, params: dict, all_pages: bool = False) -> list:
    results = []
    cursor = None
    while True:
        page_params = {**params, **({"cursor": cursor} if cursor else {})}
        resp = self.get(path, params=page_params)
        results.extend(resp.get("data", []))
        cursor = resp.get("next_cursor")
        if not all_pages or not cursor:
            break
    return results
```

Attio uses cursor-based pagination as primary with offset as fallback. Build cursor-first — offset is trivially added as a fallback branch.

### Pattern 5: Formatter Receives Raw Data, Not Formatted Strings

Commands pass raw API response dicts to the formatter. The formatter makes the `--json` vs human-readable decision.

```python
# formatter.py
def format_output(data: dict | list, as_json: bool, fields: list[str] = None):
    if as_json:
        click.echo(json.dumps(data, indent=2))
        return
    # Rich table rendering for human output
    table = Table(show_header=True)
    ...
```

Never let command code call `json.dumps()` or build Rich tables directly. That coupling makes it impossible to change output behavior without touching every command file.

---

## Data Flow

```
User types: attio records list people --limit 10 --json

1. attio_cli.py       Parses root group, loads config, creates AttioClient
                      Sets ctx.obj["client"] = AttioClient(api_key=...)

2. records.py         Receives (object_type="people", limit=10, output_json=True)
                      Calls: ctx.obj["client"].list_records("people", limit=10)

3. attio_client.py    Constructs GET /objects/people/records?limit=10
                      Checks read token bucket (100/sec)
                      Sends request via httpx.Client
                      On 429: reads Retry-After, sleeps, retries (up to 3x)
                      Returns: {"data": [...], "next_cursor": null}

4. records.py         Passes response dict + output_json=True to formatter

5. formatter.py       Detects as_json=True
                      json.dumps(response, indent=2) → click.echo

User sees JSON output.

---

REPL flow variant:

1. attio_cli.py       `attio repl` invoked
2. repl_skin.py       Starts prompt-toolkit PromptSession with history
                      Displays SKILL.md banner
                      Loops: reads user input → dispatches to Click commands
                      ctx.obj["client"] shared across all commands in session
                      Session ends on `exit` or Ctrl+D
```

---

## Build Order (Phase Dependencies)

Build in this order — each layer depends on the one below it:

```
1. CONFIG LAYER       No dependencies. Standalone. Build first.
   config.py          Must work before anything else can initialize.

2. API CLIENT LAYER   Depends on config (needs API key).
   attio_client.py    Build core HTTP + auth first.
   pagination.py      Add pagination as second step within this phase.
                      Rate limiting added here too (429 handling).

3. FORMATTER LAYER    Depends on nothing except Python stdlib + Rich.
   formatter.py       Can be built in parallel with client if needed.

4. COMMAND GROUPS     Depends on client + formatter.
   records.py etc.    Build one group end-to-end first (records) to
                      validate the full stack before building remaining 12.

5. ENTRY POINT        Depends on all command groups existing.
   attio_cli.py       Wires groups together + ctx injection.

6. REPL LAYER         Depends on entry point being complete.
   repl_skin.py       Copy from harness, wire to Click root context.

7. TESTS              Written alongside each layer (not deferred to end).
```

Records is the right first command group — it exercises the full data path (CRUD, filtering, pagination, search) and validates the entire stack before committing to the pattern across 12 more groups.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: HTTP Logic in Command Files

**What goes wrong:** Developer takes a shortcut and puts `httpx.get()` directly in `records.py` to "just make it work." Within 3 command files, auth headers, retry logic, and rate limiting are duplicated everywhere.

**Why it happens:** Faster for the first command. Catastrophic for the 12th.

**Instead:** All HTTP lives in `attio_client.py`. Commands call named methods: `client.list_records()`, `client.create_note()`. Zero HTTP code outside `utils/attio_client.py`.

### Anti-Pattern 2: Click Context as Global State

**What goes wrong:** Using a module-level singleton for the API client instead of Click's `ctx.obj`. Works fine for CLI invocation, breaks immediately in REPL mode where multiple commands share a session.

**Instead:** Always initialize `AttioClient` in the root `@click.group()` callback and inject via `ctx.obj`. The REPL inherits this context automatically.

### Anti-Pattern 3: json.dumps in Command Code

**What goes wrong:** Every command has `if output_json: click.echo(json.dumps(result, indent=2))` scattered throughout. When field ordering, indentation, or handling of None values needs to change, it's a 15-file grep-and-replace.

**Instead:** `formatter.py` is the only place that touches JSON serialization. Commands call `format_output(result, output_json)` — nothing else.

### Anti-Pattern 4: Blocking Pagination in Command Layer

**What goes wrong:** The `--all` flag logic (loop through pages until cursor is None) is implemented inside the command function. Now it's reimplemented for every command that supports listing.

**Instead:** Pagination iterator lives in `attio_client.py`. Commands pass `all_pages=True` to the client method. The command never sees cursors.

### Anti-Pattern 5: One Giant commands.py

**What goes wrong:** All 70+ endpoints in a single file. File becomes 5000+ lines, impossible to navigate, command group imports are circular, tests are impossible to isolate.

**Instead:** One file per resource group (12 files, ~200-400 lines each). Mirrors Attio's API taxonomy. Easy to add new groups without touching existing ones.

### Anti-Pattern 6: Silent Pagination Truncation

**What goes wrong:** Commands default to returning the first page only (e.g., 20 records) with no indication that more data exists. Agent gets partial data and has no way to know.

**Instead:** When results are paginated and `--all` was not passed, print a footer: `(showing 20 of N+ results — use --all to fetch all pages)`. For `--json`, include a `"truncated": true` field at the top level.

---

## Sources

- CLI-Anything HARNESS.md (official framework docs): https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/HARNESS.md
- Click Advanced Groups documentation: https://click.palletsprojects.com/en/stable/commands/
- HTTPX Client documentation: https://www.python-httpx.org/advanced/clients/
- click-repl library (prompt-toolkit integration): https://github.com/click-contrib/click-repl
- ElevenLabs Python SDK client wrapper architecture (deep reference): https://deepwiki.com/elevenlabs/elevenlabs-python/3.1-client-wrapper-system
- Python HTTP Clients comparison 2025: https://www.speakeasy.com/blog/python-http-clients-requests-vs-httpx-vs-aiohttp
- Click composable CLIs guide: https://betterstack.com/community/guides/scaling-python/click-explained/
