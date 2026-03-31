# Feature Research

**Domain:** API CLI wrapper (Attio CRM)
**Researched:** 2026-03-30
**Confidence:** HIGH — multiple authoritative sources (clig.dev, agent-CLI design guides, existing attio-cli reference, CLI-Anything framework docs)

---

## Feature Landscape

### Table Stakes

Features users expect from any serious API CLI wrapper. Missing = feels incomplete or unprofessional.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Full CRUD for all resource types | The entire value proposition — if it doesn't cover the API, it isn't a wrapper | High | 70+ endpoints across 14 resource groups. Non-negotiable. |
| `--json` flag on every command | Agent consumption and scripting require structured output. Hardcoded by clig.dev as mandatory for any CLI exposing data | Low | CLI-Anything provides this as a framework default — confirm it covers all commands |
| Meaningful exit codes | Every script and CI pipeline branches on exit codes. 0=success, non-zero=failure. Without this, shell pipelines break silently | Low | Use distinct codes: 0 success, 1 generic failure, 2 usage error, 3 not found, 4 auth failure, 5 rate limited |
| `--help` on every command | Primary discovery mechanism for both humans and AI agents. Agents run `--help` to learn what commands exist and what flags they take | Low | Click generates this automatically; requires good docstrings |
| Human-readable output by default | Humans will use this interactively. Tables or formatted text in TTY context, JSON when piped | Medium | TTY detection: if `sys.stdout.isatty()` → table; else → JSON. Eliminates need to remember `--json` |
| Pagination: `--limit` and `--all` flags | Attio API returns up to 500 per page. Any list command without pagination control is incomplete for production use | Medium | `--all` triggers automatic cursor traversal. `--limit N` caps results |
| Rate limit handling (429 retry) | Attio limits: 100 reads/sec, 25 writes/sec. 429 includes Retry-After header. CLI that crashes on 429 is unusable in automation | Low | Exponential backoff with Retry-After respect. FroeMic's attio-cli does this already |
| Auth via env var + config file | API key from `ATTIO_API_KEY` env var (for CI/agents) AND `~/.attio/config` file (for humans). Both paths required | Low | Env var takes precedence over config file. Config commands: `attio config set api-key`, `attio config get` |
| Token validation at startup | `GET /v2/self` confirms key is valid before the first real command. Surfaces auth failure with a clear message, not a cryptic 401 | Low | Auto-validate on first command, not every command (adds latency) |
| Errors to stderr, data to stdout | Non-negotiable Unix convention. Breaks pipe chains and scripting if violated | Low | `click.echo(..., err=True)` for all errors, warnings, spinners. Data only to stdout |
| Non-interactive mode (no prompts) | AI agents cannot answer confirmation prompts. All destructive operations need `--yes` / `--force` flags to bypass | Low | Never block on stdin in automation contexts. Required by agent design spec |
| REPL interactive mode | CLI-Anything requirement. Multi-command sessions without re-invoking the binary. Humans use this for exploration | Medium | CLI-Anything's ReplSkin provides this — implement correctly per framework pattern |
| Undo/redo where applicable | CLI-Anything framework expectation. Revert last write operation in REPL sessions | High | Framework provides scaffolding; implementation requires tracking state per operation. Scoped to REPL session only |
| Consistent command structure | `attio <resource> <action>` noun-verb pattern throughout. Inconsistency makes the CLI unguessable | Low | `attio people list`, `attio companies get`, `attio notes create` — never `attio list-people` |
| Filtering and sorting on list commands | Attio's API supports rich filter/sort syntax. A list command that can't filter is useless at scale | High | Pass-through to Attio's filter DSL. `--filter`, `--sort`, `--direction` flags |
| Shell completion | Bash/zsh/fish completion scripts. Expected by power users and makes the CLI dramatically faster to use | Medium | Click has `click.shell_completion` built-in. Register `attio --install-completion` |

### Differentiators

Features that set this CLI apart from the existing `attio-cli` by FroeMic and generic API wrappers. Not expected, but add real leverage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Agent-native exit codes (semantic) | Most CLIs use 0/1. Distinct codes per failure type (auth=4, rate-limit=5, not-found=3) let agents implement targeted recovery logic without parsing error strings | Low | One-time design decision. Document in `--help` output and SKILL.md |
| `--dry-run` on all write operations | Preview what would happen without committing. Critical for agent workflows where a bad write is expensive to reverse. No other Attio CLI has this | Medium | Return the payload that would be sent + expected response shape. Works via request inspection before execution |
| Structured error objects in JSON mode | When `--json` is active and a command fails, return `{"error": {"code": "...", "message": "...", "resource": "...", "field": "..."}}` to stdout instead of plain text to stderr. Agents can parse failure reasons without text matching | Low | Separate error path in JSON mode. High signal for agent recovery |
| `--output csv` format | FroeMic's CLI supports CSV. Useful for data export pipelines feeding into Clay, Google Sheets, or enrichment flows. Other formats stop at JSON/table | Low | Third output mode alongside `--json` and `--table`. Only on list/query commands |
| Batch input via stdin / `--input-file` | Accept a JSON array from stdin or file for bulk creates/updates. Enables `cat records.json | attio people create --batch` without writing a loop | Medium | NDJSON input (one record per line) is simpler to implement and stream. Flag: `--from-file records.ndjson` |
| Full OpenAPI spec coverage (no gaps) | FroeMic's CLI covers core resources but has gaps: files, webhooks, comments/threads, transcripts, workspace members, and custom object views are partial or missing. This CLI covers everything | High | This is the primary gap to exploit. 70+ endpoints vs FroeMic's ~40 |
| `attio search <query>` global search | Cross-resource search using Attio's search endpoints. "Find Mitchell Keller wherever he appears" vs having to know to search `people` specifically | Medium | Attio has a unified search endpoint. Expose it as a top-level command |
| Operation verbose mode (`--verbose`) | Show the raw HTTP request/response for debugging. Invaluable during automation development when something isn't working as expected | Low | Print `REQUEST: METHOD /path` + response status to stderr in verbose mode |
| `--fields` output projection | Filter which fields to return in output: `attio people list --fields name,email,company`. Reduces noise for agents scanning results | Medium | Server-side field filtering where Attio supports it; client-side projection otherwise |
| Session history in REPL | Arrow-up command history in interactive mode. Standard expectation for any interactive shell but few CLIs implement it well | Low | `prompt-toolkit` (CLI-Anything dependency) provides history out of the box — just wire it up properly |

### Anti-Features

Things to deliberately NOT build. Each one is a trap that either adds complexity with no proportional value, or creates maintenance burden that kills the project.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| OAuth flow | Single-workspace use (LeadGrow). OAuth adds callback server, token refresh logic, PKCE — 4x the auth complexity for zero user benefit | API key only. Document clearly in README. |
| GUI / TUI dashboard | This is a CLI. A TUI (curses, rich layout) is a separate product with separate UX rules. Mixing them creates an uncanny valley | Stay text-output. `--table` with clean formatting is sufficient for humans. |
| Webhook receiver/server | Managing webhook *subscriptions* (CRUD) is in scope. Hosting a local server to *receive* them is a separate tool (ngrok territory) | `attio webhooks create` creates the subscription. Receiving is the user's problem. |
| Caching layer | Attio's API is fast. A local cache introduces staleness bugs, invalidation complexity, and state drift. Every read should hit the API | Add `--timeout` flag if latency becomes an issue. Cache adds more problems than it solves for a CRM. |
| Computed/synthetic fields | Don't derive fields the API doesn't return (e.g., "response rate", "days since last contact"). That's analytics, not a CLI wrapper | Return exactly what Attio returns. Transformations happen downstream (jq, scripts, Clay). |
| Multi-workspace routing | Supporting N workspaces multiplies every auth and config path. LeadGrow is single-workspace. FroeMic's CLI doesn't need it either | Single workspace per config. Document workaround: multiple config profiles via `ATTIO_API_KEY` env var override. |
| Built-in scripting language | Some CLIs embed a mini-DSL for loops, conditionals over API results. This is scope creep that competes with shell scripting | Use `--json` + jq + shell. That's already a scripting layer. Don't reinvent it inside the CLI. |
| Telemetry / usage analytics | Any phone-home behavior is a trust violation for a credential-holding CLI tool | No telemetry. Ever. |
| Interactive field editors | An editor that drops into `$EDITOR` for multi-field record creation is cute but adds complexity for minimal payoff | `--field key=value` flags cover all cases. For complex JSON values, accept `@filename.json` syntax |

---

## Feature Dependencies

```
Auth (API key config + validation)
  └─ All other commands (nothing works without auth)

Pagination (cursor traversal)
  └─ Records list/query
  └─ List entries query
  └─ Notes list
  └─ Tasks list
  └─ Comments list
  └─ Files list
  └─ Meetings list
  └─ Webhooks list
  └─ Workspace Members list

Rate limit handler (429 retry)
  └─ All write operations
  └─ All read operations at volume

Records CRUD (people, companies, deals)
  └─ Notes (linked to records)
  └─ Tasks (linked to records)
  └─ Comments/Threads (linked to records)
  └─ Files (linked to records)
  └─ Meetings (linked to records)
  └─ List Entries (reference records)

Objects + Attributes
  └─ Custom Objects CRUD
  └─ List management (lists are schema-dependent)
  └─ Attribute management (options, statuses)

--json flag (framework default)
  └─ Structured error objects in JSON mode
  └─ Batch input via stdin (outputs structured results)
  └─ Agent-native exit codes (complement JSON errors)

REPL mode (CLI-Anything scaffold)
  └─ Session history
  └─ Undo/redo (scoped to REPL session)
  └─ Tab completion (enhanced in REPL context)
```

---

## MVP Definition

The MVP is "every Attio API operation accessible as a typed CLI command." That's the entire value proposition per PROJECT.md. An incomplete MVP is worse than no MVP for agent consumption — agents need to trust that if an endpoint exists, there's a command for it.

However, there's a shipping order within that constraint:

**MVP Core (Phase 1 — must ship together):**
1. Auth (env var + config file + `/v2/self` validation)
2. Rate limit handler + retry logic
3. Records CRUD: People, Companies, Deals (the primary objects)
4. List commands with `--json`, `--table`, pagination
5. `--help` on all commands
6. Meaningful exit codes

**MVP Extension (Phase 2 — completes the API surface):**
1. Notes, Tasks, Comments/Threads
2. Lists + List Entries
3. Custom Objects + Attributes
4. Files, Meetings (read), Webhooks, Workspace Members

**Differentiators (Phase 3 — after full coverage):**
1. `--dry-run` on write operations
2. Structured JSON errors
3. `--output csv`
4. Batch stdin input
5. `--fields` projection
6. Global search command

The reason for this ordering: agents break silently on missing commands. Full coverage before polish.

---

## Feature Prioritization Matrix

| Feature | Impact | Effort | Priority | Phase |
|---------|--------|--------|----------|-------|
| Auth (env var + config + validation) | Critical | Low | P0 | 1 |
| Rate limit retry (429 + Retry-After) | Critical | Low | P0 | 1 |
| Records CRUD (people/companies/deals) | Critical | High | P0 | 1 |
| `--json` flag (framework default) | Critical | Low | P0 | 1 — framework handles |
| Meaningful exit codes | High | Low | P1 | 1 |
| Human-readable default (TTY detect) | High | Low | P1 | 1 |
| Pagination (`--limit`, `--all`) | Critical | Medium | P0 | 1 |
| Shell completion | Medium | Low | P2 | 1 — Click handles |
| Notes, Tasks, Comments | High | Medium | P1 | 2 |
| Lists + List Entries | High | Medium | P1 | 2 |
| Custom Objects + Attributes | High | High | P1 | 2 |
| Files, Meetings, Webhooks, Members | Medium | High | P2 | 2 |
| REPL mode + session history | Medium | Medium | P2 | 2 — framework scaffold |
| Undo/redo in REPL | Medium | High | P2 | 2 |
| `--dry-run` on writes | High | Medium | P1 | 3 |
| Structured JSON errors | High | Low | P1 | 3 |
| `--output csv` | Medium | Low | P2 | 3 |
| Batch stdin / `--from-file` | Medium | Medium | P2 | 3 |
| `--fields` output projection | Medium | Medium | P2 | 3 |
| Global search command | Medium | Low | P2 | 3 |
| `--verbose` HTTP debug mode | Low | Low | P3 | 3 |

---

## Sources

- [Command Line Interface Guidelines (clig.dev)](https://clig.dev/) — HIGH confidence — authoritative CLI design reference
- [Writing CLI Tools That AI Agents Actually Want to Use (DEV.to)](https://dev.to/uenyioha/writing-cli-tools-that-ai-agents-actually-want-to-use-39no) — HIGH confidence — agent-specific CLI design patterns
- [CLI-Anything Framework (GitHub)](https://github.com/HKUDS/CLI-Anything) — HIGH confidence — framework constraints and built-ins
- [FroeMic/attio-cli (GitHub)](https://github.com/FroeMic/attio-cli) — HIGH confidence — existing Attio CLI reference (feature gaps identified)
- [Stripe CLI Documentation](https://docs.stripe.com/stripe-cli) — MEDIUM confidence — industry reference for API CLI design patterns
- [UX Patterns for CLI Tools (Lucas F. Costa)](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools) — MEDIUM confidence — output format and interaction patterns
- [Heroku CLI Style Guide](https://devcenter.heroku.com/articles/cli-style-guide) — MEDIUM confidence — flag design and output consistency patterns
- [AWS CLI Filtering Documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html) — MEDIUM confidence — pagination and filtering patterns in production CLIs
