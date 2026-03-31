# Requirements: Attio CLI

**Defined:** 2026-03-30
**Core Value:** Every Attio API operation accessible as a typed, documented CLI command with JSON output and interactive REPL — making Attio fully agent-controllable.

## v1 Requirements

### Infrastructure

- [x] **INFRA-01**: CLI loads API key from `ATTIO_API_KEY` env var with fallback to `~/.config/attio/config.json`
- [x] **INFRA-02**: CLI validates API key on first command via `GET /v2/self` and surfaces clear error if invalid
- [ ] **INFRA-03**: All HTTP requests go through a single AttioClient with bearer token injection, connection pooling, and timeout
- [ ] **INFRA-04**: Rate limit handling with exponential backoff on 429s, Retry-After header respect, and jitter
- [ ] **INFRA-05**: Retries on transient server errors (500/502/503/504) with backoff
- [ ] **INFRA-06**: Cursor-based pagination with `--limit N` and `--all` flags on every list command
- [ ] **INFRA-07**: Streaming output for `--all` pagination (page-by-page, no full buffer)
- [x] **INFRA-08**: `--json` flag on every command outputs raw JSON to stdout
- [x] **INFRA-09**: TTY-aware default output (Rich tables if terminal, JSON if piped)
- [x] **INFRA-10**: Errors to stderr, data to stdout (Unix convention)
- [x] **INFRA-11**: Semantic exit codes: 0=success, 1=generic error, 2=usage error, 3=not found, 4=auth failure, 5=rate limited
- [x] **INFRA-12**: `--help` on every command and subcommand with accurate descriptions
- [x] **INFRA-13**: Shell completion for bash/zsh/fish via Click 8 built-in
- [x] **INFRA-14**: Authorization header redacted from all error output and logs

### Records

- [ ] **REC-01**: User can create a record on any standard object (people, companies, deals, users, workspaces) via `attio <object> create`
- [ ] **REC-02**: User can get a single record by ID via `attio <object> get <id>`
- [ ] **REC-03**: User can list/query records with filter and sort via `attio <object> list`
- [ ] **REC-04**: User can update a record via PATCH (append multiselect) via `attio <object> update <id>`
- [ ] **REC-05**: User can overwrite a record via PUT (replace multiselect) via `attio <object> update <id> --overwrite`
- [ ] **REC-06**: User can delete a record via `attio <object> delete <id>`
- [ ] **REC-07**: User can assert (create-or-update) a record via `attio <object> assert --matching-attribute <slug>`
- [ ] **REC-08**: User can fuzzy search records via `attio <object> search <query>`
- [ ] **REC-09**: Simple filter shorthand `--filter key=value` for common cases
- [ ] **REC-10**: File-based complex filters via `--filter-file filters.json`

### Notes

- [ ] **NOTE-01**: User can create a note on a record via `attio notes create`
- [ ] **NOTE-02**: User can get a note by ID via `attio notes get <id>`
- [ ] **NOTE-03**: User can list notes (all or filtered by record) via `attio notes list`
- [ ] **NOTE-04**: User can update a note via `attio notes update <id>`
- [ ] **NOTE-05**: User can delete a note via `attio notes delete <id>`

### Tasks

- [ ] **TASK-01**: User can create a task with assignees and linked records via `attio tasks create`
- [ ] **TASK-02**: User can get a task by ID via `attio tasks get <id>`
- [ ] **TASK-03**: User can list tasks (filtered by record, assignee, status) via `attio tasks list`
- [ ] **TASK-04**: User can update a task (deadline, completion, assignees) via `attio tasks update <id>`
- [ ] **TASK-05**: User can delete a task via `attio tasks delete <id>`

### Comments & Threads

- [ ] **CMNT-01**: User can create a comment on a thread, record, or entry via `attio comments create`
- [ ] **CMNT-02**: User can get a comment by ID via `attio comments get <id>`
- [ ] **CMNT-03**: User can delete a comment via `attio comments delete <id>`
- [ ] **CMNT-04**: User can resolve/unresolve a comment thread via `attio comments resolve/unresolve <id>`
- [ ] **CMNT-05**: User can list threads on a record or entry via `attio threads list`
- [ ] **CMNT-06**: User can get a thread with all comments via `attio threads get <id>`

### Lists

- [ ] **LIST-01**: User can list all lists via `attio lists list`
- [ ] **LIST-02**: User can get a list by ID via `attio lists get <id>`
- [ ] **LIST-03**: User can create a list via `attio lists create`
- [ ] **LIST-04**: User can update a list via `attio lists update <id>`
- [ ] **LIST-05**: User can list views for a list via `attio lists views <id>`

### List Entries

- [ ] **ENTRY-01**: User can create an entry in a list via `attio entries create`
- [ ] **ENTRY-02**: User can get an entry by ID via `attio entries get <id>`
- [ ] **ENTRY-03**: User can list/query entries with filter and sort via `attio entries list`
- [ ] **ENTRY-04**: User can update an entry (PATCH append) via `attio entries update <id>`
- [ ] **ENTRY-05**: User can overwrite an entry (PUT replace) via `attio entries update <id> --overwrite`
- [ ] **ENTRY-06**: User can delete an entry via `attio entries delete <id>`
- [ ] **ENTRY-07**: User can assert an entry by parent record via `attio entries assert`

### Objects & Attributes

- [ ] **OBJ-01**: User can list all objects via `attio objects list`
- [ ] **OBJ-02**: User can get an object by ID or slug via `attio objects get <id>`
- [ ] **OBJ-03**: User can create a custom object via `attio objects create`
- [ ] **OBJ-04**: User can update an object via `attio objects update <id>`
- [ ] **OBJ-05**: User can list views for an object via `attio objects views <id>`
- [ ] **ATTR-01**: User can list attributes on an object or list via `attio attributes list --object <slug>`
- [ ] **ATTR-02**: User can create an attribute via `attio attributes create`
- [ ] **ATTR-03**: User can update an attribute via `attio attributes update <id>`
- [ ] **ATTR-04**: User can archive an attribute via `attio attributes archive <id>` (NOT delete)
- [ ] **ATTR-05**: User can manage select options via `attio attributes options`
- [ ] **ATTR-06**: User can manage status values via `attio attributes statuses`

### Files

- [ ] **FILE-01**: User can upload a file to a record via `attio files upload`
- [ ] **FILE-02**: User can get file metadata by ID via `attio files get <id>`
- [ ] **FILE-03**: User can list files (filtered by record) via `attio files list`
- [ ] **FILE-04**: User can download a file via `attio files download <id>`
- [ ] **FILE-05**: User can delete a file via `attio files delete <id>`
- [ ] **FILE-06**: User can create a folder via `attio files create-folder`

### Meetings

- [ ] **MEET-01**: User can list meetings via `attio meetings list`
- [ ] **MEET-02**: User can get a meeting by ID via `attio meetings get <id>`
- [ ] **MEET-03**: User can list call recordings for a meeting via `attio meetings recordings <id>`
- [ ] **MEET-04**: User can get a call transcript via `attio meetings transcript <recording-id>`

### Webhooks

- [ ] **HOOK-01**: User can create a webhook subscription via `attio webhooks create`
- [ ] **HOOK-02**: User can get a webhook by ID via `attio webhooks get <id>`
- [ ] **HOOK-03**: User can list all webhooks via `attio webhooks list`
- [ ] **HOOK-04**: User can update a webhook via `attio webhooks update <id>`
- [ ] **HOOK-05**: User can delete a webhook via `attio webhooks delete <id>`

### Workspace

- [ ] **WORK-01**: User can list workspace members via `attio workspace members`
- [ ] **WORK-02**: User can get a workspace member by ID via `attio workspace member <id>`
- [ ] **WORK-03**: User can identify current token/workspace via `attio workspace self`

### REPL & Polish

- [ ] **REPL-01**: User can start interactive REPL via `attio repl` with persistent context
- [ ] **REPL-02**: REPL supports command history (arrow-up) saved to `~/.config/attio/history`
- [ ] **REPL-03**: REPL supports tab completion of commands and subcommands
- [ ] **REPL-04**: REPL continues on command errors (shows error, returns to prompt)
- [ ] **REPL-05**: Non-interactive mode via `--yes` flag bypasses all confirmation prompts

### Testing

- [ ] **TEST-01**: Unit tests for AttioClient (auth, rate limiting, pagination, retry)
- [ ] **TEST-02**: Unit tests for all command groups (Click CliRunner)
- [ ] **TEST-03**: Unit tests for formatter (JSON output, table rendering)
- [ ] **TEST-04**: E2E tests against live Attio API (LeadGrow workspace)
- [ ] **TEST-05**: CI-ready test suite (no real API calls in unit tests via pytest-httpx)

### Documentation

- [ ] **DOC-01**: SKILL.md generated for AI agent discovery
- [ ] **DOC-02**: ATTIO.md SOP document with usage examples
- [ ] **DOC-03**: setup.py with entry_points for `cli-anything-attio` command

## v2 Requirements

### Agent Differentiators

- **DIFF-01**: `--dry-run` on all write operations (preview payload without executing)
- **DIFF-02**: Structured JSON error objects in JSON mode (`{"error": {"code": "...", "message": "...", "resource": "..."}}`)
- **DIFF-03**: `--output csv` format on list/query commands
- **DIFF-04**: Batch input via stdin or `--from-file records.ndjson` for bulk creates/updates
- **DIFF-05**: `--fields` output projection (filter which fields appear in output)
- **DIFF-06**: `attio search <query>` global cross-resource search command
- **DIFF-07**: `--verbose` mode showing raw HTTP request/response for debugging

### Undo/Redo

- **UNDO-01**: Undo last write operation in REPL session
- **UNDO-02**: Redo undone operation in REPL session

## Out of Scope

| Feature | Reason |
|---------|--------|
| OAuth flow | Single-workspace use (LeadGrow). API key auth only. |
| SCIM provisioning | Enterprise-only feature not used by LeadGrow |
| GUI / TUI dashboard | This is a CLI. Rich tables are sufficient for humans. |
| Webhook receiver/server | CLI manages subscriptions. Receiving events is a separate tool. |
| Caching layer | CRM data changes frequently. Cache = staleness bugs. Every read hits API. |
| Multi-workspace routing | Single workspace per config. Multiple configs via env var override. |
| Computed/synthetic fields | Return exactly what Attio returns. Transformations happen downstream. |
| Embedded scripting | Use --json + jq + shell. Don't reinvent scripting inside the CLI. |
| Telemetry | Trust violation for credential-holding CLI. Never. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 through INFRA-14 | Phase 1 | Pending |
| REC-01 through REC-10 | Phase 1 | Pending |
| NOTE-01 through NOTE-05 | Phase 2 | Pending |
| TASK-01 through TASK-05 | Phase 2 | Pending |
| CMNT-01 through CMNT-06 | Phase 2 | Pending |
| LIST-01 through LIST-05 | Phase 2 | Pending |
| ENTRY-01 through ENTRY-07 | Phase 2 | Pending |
| OBJ-01 through OBJ-05 | Phase 2 | Pending |
| ATTR-01 through ATTR-06 | Phase 2 | Pending |
| FILE-01 through FILE-06 | Phase 2 | Pending |
| MEET-01 through MEET-04 | Phase 2 | Pending |
| HOOK-01 through HOOK-05 | Phase 2 | Pending |
| WORK-01 through WORK-03 | Phase 2 | Pending |
| REPL-01 through REPL-05 | Phase 3 | Pending |
| TEST-01 through TEST-05 | Phase 3 | Pending |
| DOC-01 through DOC-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 81 total
- Mapped to phases: 81
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 after initial definition*
