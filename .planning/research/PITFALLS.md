# Pitfalls Research

**Domain:** API CLI wrapper (Attio CRM REST API v2)
**Researched:** 2026-03-30
**Confidence:** HIGH (Attio-specific facts verified against official docs; general CLI patterns verified against multiple community sources)

---

## Critical Pitfalls

These cause data loss, silent corruption, or rewrites if not addressed in the initial implementation.

---

### Pitfall 1: PUT vs PATCH Confusion — Multiselect Data Loss

**What goes wrong:** Using PUT when PATCH is intended (or vice versa) on multiselect and multi-value attributes silently destroys data. PUT on a record's multiselect attribute replaces all existing values with the supplied list. PATCH appends. If a command sends PUT when the user says "add a tag," every other tag on that record is erased. No error is thrown — the operation succeeds with a 200.

**Why it happens:** PUT and PATCH look symmetric in the CLI surface. Developers wire up "update record" to PUT by default because it's the obvious HTTP verb for "update." The distinction only becomes obvious when reading Attio's assert behavior docs carefully: for multiselect attributes, the matching attribute values are additive (existing values not deleted), but any other multiselect attribute in the PUT payload is treated as a full replacement.

**Consequences:** Silent data loss. User runs `attio records update company --add-tag vip` and unknowingly wipes the company's `tags` list down to just `vip`. No error, no warning, 200 OK. Discovered hours or days later when data is gone.

**Prevention:**
- Expose PUT and PATCH as distinct commands or flags at the CLI level, not unified behind "update"
- Add a `--mode overwrite|append` flag for multi-value attributes on any write operation
- Document the verb semantics explicitly in `--help` output, not just in README
- Default to PATCH for partial updates; require explicit `--overwrite` opt-in for PUT behavior
- Add a warning to stdout when PUT is issued on an object with known multiselect attributes

**Warning signs:** "Update" command working without errors but record state inconsistent; users reporting tags/multi-values disappearing after updates

**Phase to address:** Phase 1 (Records CRUD foundation) — must be resolved before any update command ships

---

### Pitfall 2: Assert Matching Attribute Multiselect Exception

**What goes wrong:** The assert endpoint (PUT /v2/objects/{object}/records with matching_attribute) has a documented exception: if the matching attribute IS a multiselect attribute, new values are added and existing values are NOT deleted. But for all OTHER multiselect attributes in the same payload, values are created or deleted to match what's supplied. This asymmetry is invisible at the call site.

**Why it happens:** The exception is buried in Attio's assert documentation and seems counterintuitive. Developers assume one rule applies uniformly. The matching attribute gets additive behavior; the payload attributes get replacement behavior.

**Consequences:** Assert operations produce inconsistent results depending on which attribute is used as the matching key. Debugging this without knowing the rule is a nightmare — the same payload behaves differently based on matching_attribute choice.

**Prevention:**
- Document this asymmetry explicitly in the `assert` command's `--help` text
- When `--matching-attribute` is a multiselect attribute, emit a warning about the additive matching vs replacement payload behavior
- Add a specific integration test that validates assert behavior on a record with multiple multiselect attributes

**Warning signs:** Assert producing unexpected results; duplicate values appearing in non-matching multiselect attributes

**Phase to address:** Phase 1 (Records CRUD, assert command)

---

### Pitfall 3: Score-Based Rate Limiting Is Not Just Request Count

**What goes wrong:** The implementation handles HTTP 429 by checking request count against 100 reads/sec and 25 writes/sec. But Attio applies a second, more restrictive layer: complexity scoring on List records and List entries endpoints. Queries with complex filters/sorts or against large object collections receive high complexity scores. Multiple such queries within a 10-second sliding window get throttled even if they're under the raw request-per-second limit.

**Why it happens:** The score-based limits aggregate across ALL apps and access tokens on the workspace — including other integrations running against the same Attio workspace. Even if the CLI alone is within limits, other integrations (Zapier, native integrations, etc.) consume score budget. The CLI cannot observe this.

**Consequences:** 429s appear sporadically on complex queries even at low request rates. Naive retry logic that only uses Retry-After for basic rate limits will keep re-triggering the score limit if it reduces complexity factors. No backoff on the query itself.

**Prevention:**
- Implement exponential backoff on 429s, not just Retry-After sleep — the score window is 10 seconds, but repeated complex queries will immediately hit it again on resume
- Add a `--complexity low` flag or warn users when filter/sort complexity is high
- Separate retry logic for score-based vs request-based 429s (check error body `"code": "rate_limit_exceeded"` and `"type": "rate_limit_error"`)
- When `--all` flag is used to paginate through all records on a large object, add configurable delay between pages to stay under the score window

**Warning signs:** 429s occurring at low request rates; sporadic throttling on `list` commands; throttling that resumes immediately after Retry-After wait

**Phase to address:** Phase 1 (infrastructure/HTTP client setup) — retry logic must be correct from day one

---

### Pitfall 4: `--all` Flag Memory Bomb on Large Objects

**What goes wrong:** A `--all` pagination flag that silently accumulates all pages into memory before outputting works fine on small objects (100 records) and explodes on large ones (50,000+ companies). No progress feedback, potential OOM, no way to interrupt cleanly without losing partial results.

**Why it happens:** The natural implementation is `while next_cursor: fetch_page(); results.extend(page)`. This works. It just doesn't scale. Developers test against small datasets, ship, and discover the problem when a user runs `attio records list companies --all` against a workspace with 80,000 company records.

**Consequences:** OOM crash mid-pagination, lost partial output, frustrated users. With Attio's default limit of 500 per page and a 25ms inter-page delay at 100 req/sec limit, 80k records = 160 pages = 4 seconds of wall time but 160 full page objects in memory simultaneously.

**Prevention:**
- Stream output page-by-page when `--json` flag is combined with `--all` — emit each record as it arrives, don't buffer
- Add `--max-records N` as a hard safety cap with a default (e.g., 10,000) that requires explicit override
- Show progress during pagination: `Fetching... (2,500 / ~unknown)` — use stderr so it doesn't corrupt stdout JSON
- For `--all` without `--json`, stream to stdout as records arrive (newline-delimited or pretty-printed)

**Warning signs:** `--all` working fine in tests (small dataset), memory growth proportional to result count, no progress feedback

**Phase to address:** Phase 1 (pagination infrastructure) — stream-by-default before any `--all` flag ships

---

### Pitfall 5: Filter Syntax Complexity — JSON Strings in Shell

**What goes wrong:** Attio's filter syntax is a nested JSON structure with `$and`, `$or`, `$not` operators, attribute-specific comparison operators (`$eq`, `$contains`, `$gt`, etc.), and path-drilling for record-references. Passing this as a CLI argument means users are writing JSON strings in shell — where quote escaping, newlines, and special characters create a minefield. `--filter '{"name": {"$eq": "Acme"}}'` works in a bash script; the same thing in PowerShell, fish, or via Python's `subprocess` does not.

**Why it happens:** It's tempting to just accept `--filter` as a raw JSON string because it maps directly to the API. But every shell has different quoting rules, and `$and` is particularly nasty because `$` is shell variable expansion in bash/zsh.

**Consequences:** Users can't use complex filters. Bugs reported as "filter broken" that are actually shell-escaping issues. Frustrating to debug because the error messages from Attio on malformed filter JSON are cryptic 400s.

**Prevention:**
- Accept filters as a JSON file path (`--filter-file filters.json`) as the primary interface for complex filters
- Accept simple key=value pairs as shorthand (`--filter name=Acme`) that the CLI converts to `{"name": {"$eq": "Acme"}}`
- When parsing filter JSON fails, emit a helpful error with an example of correctly escaped syntax for common shells
- In REPL mode, provide filter builder with tab completion that avoids shell escaping entirely
- Wrap `$` operators in the documentation with shell-escaping examples for bash, zsh, and PowerShell

**Warning signs:** Users can do simple filters but not complex ones; bug reports about `$and` filters failing; 400 errors that are actually escape issues

**Phase to address:** Phase 1 for basic filters; Phase 2+ for complex path/drill-down filters in REPL

---

## Technical Debt Patterns

### Pattern 1: One HTTP Client Per Command Instead of Shared Client

**What goes wrong:** Each Click command instantiates its own `requests.Session()` or HTTP client instead of sharing one configured client. Rate limit state, retry logic, and auth headers get duplicated across 70+ commands.

**Prevention:** Create a single `AttioClient` class injected via Click's `pass_context` pattern. All rate limiting, retry backoff, auth header injection, and base URL configuration live in one place. Every command calls `ctx.obj.client.get(...)`.

**Phase to address:** Phase 1 (foundational infrastructure, before any endpoint commands ship)

---

### Pattern 2: Attribute Slug Drift — Hardcoded Slugs That Break

**What goes wrong:** Commands hardcode attribute slugs (`email_addresses`, `phone_numbers`) that were valid when written. Workspace admins rename custom attributes. The slug changes. The command silently fails with a 400 or returns empty results.

**Prevention:**
- Never hardcode attribute slugs for custom attributes in command logic
- For standard system attributes (email_addresses, name, etc.), document that these are Attio system slugs unlikely to change
- Provide an `attio attributes list --object people` discovery command so users can always look up current slugs
- When a 400 is received on an attribute reference, emit a hint: "Attribute slug may have changed — run `attio attributes list` to verify"

**Phase to address:** Phase 2 (Attributes commands) — discovery commands must ship before attribute-dependent commands

---

### Pattern 3: OpenAPI Spec as Source of Truth for Types Only

**What goes wrong:** Attio provides a machine-readable OpenAPI spec at https://api.attio.com/openapi/api. It's tempting to auto-generate the entire client from it. Generated clients have terrible CLI ergonomics: parameter names match API parameter names (snake_case_with_underscores), help text is auto-generated and generic, and complex types get serialized as opaque strings users can't understand.

**Prevention:**
- Use the OpenAPI spec for type validation and request/response shape verification in tests only
- Write commands by hand with UX-first parameter names
- Run spec validation in CI to catch API changes early (new required fields, deprecated endpoints)
- Do NOT code-generate the CLI layer — the UX won't be AI-agent-friendly or human-friendly

**Phase to address:** Phase 1 (tooling setup)

---

### Pattern 4: REPL State Leaking Between Commands

**What goes wrong:** REPL mode maintains a Click context across commands. If a command modifies shared mutable state (pagination cursor from a previous list command, a cached auth token, a filter state), subsequent unrelated commands see stale or wrong state.

**Prevention:**
- Make each REPL command invocation fully stateless relative to prior commands — no shared mutable state between commands except explicit session-level config (auth token, workspace ID)
- Store REPL history and tab-completion state separately from API client state
- Test that running `list`, then `get`, then `list` again produces clean results with no cursor leak

**Phase to address:** Phase 2 (REPL implementation)

---

## Integration Gotchas

### Gotcha 1: ID vs Slug Resolution on Records

Records can be referenced by either UUID (`rec_abc123`) or string slug. Some endpoints accept both; some only accept one form. The CLI must handle both transparently and emit a clear error when the wrong form is used.

**Specific issue:** List entries use entry IDs that look like UUIDs but are distinct from record IDs. A user passing a record ID to a list entry endpoint gets a confusing 404, not a "wrong ID type" message.

**Prevention:** Validate ID format before the API call. If a UUID is expected and a slug is passed, surface a clear error with `--help` pointing to the right lookup command.

---

### Gotcha 2: Attribute Types Have Type-Specific Write Formats

Attio has 17 attribute types. Each has a distinct JSON write format. Writing an email address requires `{"email_address": "foo@bar.com"}` not `"foo@bar.com"`. Writing a record-reference requires `{"target_record_id": "..."}` not the record slug. Writing a location requires a nested object with `line_1`, `city`, `state`, etc.

Users will try to write raw values. The errors returned by Attio on format mismatch are typically 422s with messages like "invalid value for attribute type" — not "expected object with key email_address."

**Prevention:**
- Build type-aware value coercion into each attribute write path
- For known attribute types, accept simplified input and coerce to the API format internally (e.g., `--email foo@bar.com` → `{"email_address": "foo@bar.com"}`)
- Emit validation errors before the API call when the input clearly doesn't match the expected type format
- Document type-specific input formats in each command's `--help` output

---

### Gotcha 3: Attributes Cannot Be Deleted — Only Archived

The Attio API does not support attribute deletion via the REST API. Attributes can only be archived. Any `attio attributes delete` command would need to call the archive endpoint, not a delete endpoint. If implemented as DELETE it will 404 or 405.

**Prevention:** Name the command `attio attributes archive` not `attio attributes delete`. Document this explicitly.

---

### Gotcha 4: Cursor Pagination — No "Total Count" Signal

Attio's cursor pagination does not return a total record count. There is no `total: 5000` in the response. The end-of-results signal is the absence of `next_cursor`. This means:

- Progress bars require estimation or are impossible
- `--limit N` means "up to N records" not "exactly N records" when fewer exist
- The end condition for offset pagination is "received fewer results than the limit" — a response with exactly 500 results could be the last page OR have more

**Prevention:**
- Do not promise total counts in output; use `Fetching...` progress instead of `X of Y`
- For offset pagination end detection: treat `len(results) < limit` as end signal; treat `len(results) == limit` as "may have more, fetching next page"
- Document the absence of total count in `--help` output so users understand why progress is indeterminate

---

### Gotcha 5: Score-Based Limits Aggregate Across All API Tokens

Attio's score-based rate limits aggregate across ALL apps and access tokens on the workspace. If the LeadGrow workspace has Zapier, native integrations, or other CLIs running simultaneously, the CLI shares their score budget. The CLI can hit 429s without having made any requests itself.

**Prevention:**
- Always implement exponential backoff on 429s, not just Retry-After sleep
- Log a warning when a 429 is received: "Rate limit hit — this may be caused by other integrations on this workspace"
- Never assume 429 = "I sent too many requests"

---

## Performance Traps

### Trap 1: N+1 Requests for Record Display With Related Data

Fetching a list of records and then individually fetching related record attributes (e.g., company for each person) creates N+1 request patterns. With 100 people each associated with a company, that's 101 requests where 1-2 would suffice.

**Prevention:** Design list commands to retrieve only the fields requested. Use Attio's field selection parameters if available. Warn users when `--expand` flags would trigger high request counts.

---

### Trap 2: File Upload Memory: Loading Entire File Before POST

The file upload endpoint requires a POST with the file content. Loading large files entirely into memory before POSTing is fine for small attachments, catastrophic for large files.

**Prevention:** Use streaming upload for files — `requests` supports `files={"file": open(path, "rb")}` which streams from disk. Never `open().read()` before uploading.

---

## Security Mistakes

### Mistake 1: API Key in Command History

If the API key can be passed as `--api-key YOUR_SECRET_KEY`, it appears in shell history, process listings (`ps aux`), and CI logs.

**Prevention:**
- Accept API key ONLY via environment variable (`ATTIO_API_KEY`) or config file
- If `--api-key` flag is ever added, strip it from any logging immediately and add a deprecation warning
- Config file storage: use `~/.config/attio/config.json` with 0600 permissions, never in the project directory

---

### Mistake 2: Config File in Project Directory Gets Committed

Config files created in the working directory (`.attio`, `attio.json`, `.env`) get accidentally committed to git, leaking API keys.

**Prevention:**
- Store config in `~/.config/attio/` (XDG base directory standard), not in the working directory
- Document the config location clearly; never write config to CWD
- Add `.attio` to the project's `.gitignore` as a safety net even if the tool doesn't use that path

---

### Mistake 3: Verbose Error Logging Leaks Tokens

Exception handlers that log the full request object (including `Authorization: Bearer ...` headers) to stdout/stderr leak the API key in error output.

**Prevention:**
- Redact `Authorization` headers before any logging: replace with `Authorization: Bearer [REDACTED]`
- Never log raw request objects; log sanitized summaries only

---

## "Looks Done But Isn't" Checklist

These items make the CLI appear complete but fail in real use:

- [ ] **Pagination stops at page 1** — `--all` flag wired but loop exits on empty page, not missing cursor
- [ ] **Retry logic only covers 429** — 500/503 errors from Attio's infrastructure are not retried
- [ ] **Update command silently uses PUT** — multiselect values disappear, no error surfaced
- [ ] **Filter JSON 400s return API error verbatim** — `"filter.0.condition.attribute_type.value must be a string"` is not actionable for users
- [ ] **REPL exits on any error** — instead of showing the error and returning to prompt
- [ ] **`--json` output includes ANSI color codes** — breaks downstream JSON parsing by agents
- [ ] **Cursor from page N used in a subsequent different query** — cursor is query-scoped but code reuses last cursor
- [ ] **No validation of `ATTIO_API_KEY` presence at startup** — first failed request shows cryptic 401 instead of "API key not configured"
- [ ] **Exit codes not set** — all commands exit 0 even on API error; agent scripts can't detect failure
- [ ] **`--all` with large dataset has no interruption handling** — Ctrl+C during pagination corrupts partial output
- [ ] **Attribute archive labeled as delete** — command 404s because DELETE endpoint doesn't exist for attributes
- [ ] **Record ID format not validated** — passing slug to ID-only endpoint returns confusing 404

---

## Pitfall-to-Phase Mapping

| Phase Topic | Pitfall | Mitigation |
|-------------|---------|------------|
| Phase 1: HTTP client / auth | API key in history | Env var only, no --api-key flag |
| Phase 1: HTTP client / auth | Verbose error leaks token | Redact Authorization header before logging |
| Phase 1: HTTP client / auth | Startup config validation | Check ATTIO_API_KEY presence at import time, fail fast with clear message |
| Phase 1: Rate limiting | Score-based 429s not just count-based | Exponential backoff, warn about workspace-shared budget |
| Phase 1: Rate limiting | 500/503 not retried | Retry on 500/502/503/504 with backoff, not just 429 |
| Phase 1: Pagination | `--all` memory bomb | Stream output, add --max-records safety cap |
| Phase 1: Pagination | Offset end detection off-by-one | Treat count == limit as "may have more", count < limit as end |
| Phase 1: Records CRUD | PUT vs PATCH data loss | Separate commands, default to PATCH, require explicit overwrite flag |
| Phase 1: Records CRUD | Assert multiselect asymmetry | Document and warn in --help, dedicated integration test |
| Phase 1: Shared client | N+1 HTTP clients | Single AttioClient via Click context, injected everywhere |
| Phase 2: Filtering | Shell quoting on JSON filters | --filter-file as primary, key=value shorthand for simple cases |
| Phase 2: Attributes | Slug drift | Discovery commands before attribute-dependent commands ship |
| Phase 2: Attributes | Attribute type write formats | Type-aware coercion with helpful validation errors |
| Phase 2: Attributes | Archive labeled as delete | Name command `archive`, not `delete` |
| Phase 2: REPL | State leak between commands | Stateless per-command invocation, REPL continues on error |
| Phase 2: REPL | ANSI in --json output | Never emit ANSI when stdout is not a TTY or --json is set |
| All phases | Exit codes not set | Every command sets non-zero exit code on API error |
| All phases | OpenAPI spec drift | CI validates against live spec to catch required field changes |

---

## Sources

- [Attio Rate Limiting Guide](https://docs.attio.com/rest-api/guides/rate-limiting) — Score-based limits, sliding window, 429 behavior (HIGH confidence)
- [Attio Pagination Guide](https://docs.attio.com/rest-api/guides/pagination) — Cursor vs offset, end-of-results signals (HIGH confidence)
- [Attio Assert Endpoint](https://docs.attio.com/rest-api/endpoint-reference/workspaces/assert-a-workspace-record) — Multiselect matching attribute exception (HIGH confidence)
- [Attio Attribute Types Overview](https://docs.attio.com/docs/attribute-types/attribute-types) — 17 attribute types, is_multiselect, type-specific behavior (HIGH confidence)
- [Attio Filtering and Sorting](https://docs.attio.com/rest-api/how-to/filtering-and-sorting) — $and/$or/$not operators, path filtering, comparison operators (HIGH confidence)
- [FroeMic/attio-cli (existing TypeScript Attio CLI)](https://github.com/FroeMic/attio-cli) — Attribute archive limitation, PUT/PATCH patterns, output format lessons (MEDIUM confidence, community project)
- [API Platform cursor pagination issue](https://github.com/api-platform/api-platform/issues/2087) — Cursor invalidation edge cases (MEDIUM confidence)
- [Mux OpenAPI code generation experience](https://www.mux.com/blog/an-adventure-in-openapi-v3-api-code-generation) — OpenAPI generation vs hand-written tradeoffs (MEDIUM confidence)
- [click-repl compatibility issue #71](https://github.com/click-contrib/click-repl/issues/71) — REPL mode instability with args/options in prompt-toolkit 2.0+ (MEDIUM confidence)
- [GitGuardian Python secrets management](https://blog.gitguardian.com/how-to-handle-secrets-in-python/) — Config file and env var security patterns (MEDIUM confidence)
