# Project Research Summary

**Project:** Attio CLI
**Domain:** API CLI wrapper (Attio CRM REST API v2)
**Researched:** 2026-03-30
**Confidence:** HIGH

## Executive Summary

This is a Python CLI wrapping the Attio CRM REST API v2 (~70+ endpoints, 15 resource groups) using the CLI-Anything framework. The stack is locked: Python 3.10+, Click 8.3+, httpx 0.28+, prompt-toolkit 3.0+, Rich 14+, tenacity 9+. No ambiguous technology decisions remain.

The architecture is five layers (config > client > formatter > commands > entry point) with REPL on top. The critical insight from research: build records end-to-end first (all layers, one resource group) to validate the full stack before replicating across 11 more groups. The pattern is write-once, repeat-many.

Three risks dominate: (1) PUT vs PATCH multiselect data loss (silent 200, data gone), (2) score-based rate limiting that aggregates across all workspace integrations (not just request count), and (3) `--all` pagination memory bombs on large datasets. All three must be solved in the foundation phase before any commands ship.

## Key Findings

### Recommended Stack

Fully locked. No alternatives to evaluate.

**Core:** Python 3.10+, Click 8.3.1, httpx 0.28.1, prompt-toolkit 3.0.52, Rich 14.3.3, tenacity 9.1.4, python-dotenv 1.2.2
**Supporting:** rich-click 1.9+, click-repl 0.3.0, pytest-httpx 0.35+
**Dev:** uv (package mgmt), ruff (lint/format), mypy (types), pytest-cov

**What NOT to use:** requests (no transport layer for mocking), aiohttp (async-only), typer (breaks CLI-Anything patterns), pydantic-settings (overkill for one env var), click-completion (abandoned, use Click 8 built-in)

### Expected Features

**Table stakes (must have):**
- Full CRUD for all 15 resource groups
- `--json` on every command (framework default)
- Semantic exit codes (0/1/2/3/4/5)
- TTY-aware output (table if terminal, JSON if piped)
- Pagination with `--limit` and `--all`
- 429 retry with exponential backoff
- Auth via env var + config file
- REPL mode (CLI-Anything requirement)
- Shell completion (Click 8 built-in)
- `--help` on every command

**Differentiators (competitive advantage over FroeMic's attio-cli):**
- Full API coverage (70+ endpoints vs ~40)
- `--dry-run` on write operations
- Structured JSON error objects
- CSV output mode
- Batch input via stdin/file
- `--fields` output projection
- Global search command
- `--verbose` HTTP debug mode

**Anti-features (explicitly cut):**
- OAuth flow, TUI/GUI, webhook receiver, caching, multi-workspace, embedded scripting, telemetry

### Architecture Approach

Five layers with strict boundaries. One file per resource group (12 files). Single AttioClient injected via Click context. Formatter receives raw data, never formatted strings. Pagination invisible to command layer.

**Build order:** Config > Client (HTTP + auth + rate limit + pagination) > Formatter > One command group end-to-end (records) > Remaining 11 groups > REPL > Tests alongside each layer

### Critical Pitfalls

1. **PUT vs PATCH data loss** — Default to PATCH for updates; require explicit `--overwrite` flag for PUT. Never unify behind "update" without distinguishing verbs.
2. **Score-based rate limiting** — Exponential backoff, not just Retry-After. Score budget is shared across all workspace integrations.
3. **`--all` memory bomb** — Stream output page-by-page. Never buffer all pages before output.
4. **Assert multiselect asymmetry** — Matching attribute is additive; payload attributes are replacement. Document and warn.
5. **Filter syntax + shell quoting** — `--filter-file` as primary interface; `key=value` shorthand for simple filters.
6. **Attributes can't be deleted** — Only archived. Name command `archive` not `delete`.

## Implications for Roadmap

### Phase 1: Foundation + Core Records
**Rationale:** All layers must exist before any command works. Records (people/companies/deals) exercise the full data path (CRUD, pagination, filtering, search, assert).
**Delivers:** Working CLI with auth, HTTP client, formatter, records CRUD, pagination, rate limiting, exit codes
**Addresses:** Auth, Records CRUD, Pagination, Rate Limiting, JSON output, Exit codes
**Avoids:** PUT/PATCH confusion (separate from day one), memory bomb (streaming pagination), score-based rate limits

### Phase 2: Complete API Surface
**Rationale:** Full coverage before polish. Agents need to trust that if an endpoint exists, there's a command. Pattern is established from Phase 1 — this is repetition.
**Delivers:** All remaining resource groups (notes, tasks, lists, entries, comments, attributes, objects, files, meetings, webhooks, members)
**Addresses:** Notes/Tasks/Comments, Lists/Entries, Objects/Attributes, Files/Meetings, Webhooks/Members

### Phase 3: REPL + Agent Differentiators
**Rationale:** Polish and differentiation after coverage is complete. REPL requires all commands to exist. Differentiators add value on top of a complete foundation.
**Delivers:** REPL mode, dry-run, structured errors, CSV output, batch input, field projection, global search, verbose mode
**Addresses:** REPL, undo/redo, all differentiator features

### Phase Ordering Rationale

- Phase 1 before 2: Can't build commands without the HTTP client and formatter layers
- Phase 2 before 3: REPL needs all commands registered; differentiators are pointless without coverage
- Records first within Phase 1: Exercises every architectural pattern (CRUD, query, filter, assert, search)

### Research Flags

Phases with standard patterns (skip deep research):
- **Phase 2:** Pure command repetition of Phase 1 pattern. No architectural decisions.
- **Phase 3:** REPL is CLI-Anything standard. Differentiator features are well-understood patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI. No contested decisions. |
| Features | HIGH | Corroborated across clig.dev, agent CLI guides, FroeMic gap analysis |
| Architecture | HIGH | CLI-Anything patterns + Click best practices converge on same design |
| Pitfalls | HIGH | Attio-specific gotchas verified against official docs |

**Overall confidence:** HIGH

### Gaps to Address

- pytest-httpx 0.35+ compatibility with httpx 0.28.1 — verify before first test run
- CLI-Anything undo/redo scaffolding — verify exactly what framework provides vs what we implement
- Attio `--dry-run` support — check if API has any dry-run headers; likely client-side only

## Sources

### Primary (HIGH confidence)
- Attio API documentation (rate limiting, pagination, attributes, assert) — verified against official docs
- CLI-Anything framework (HARNESS.md, CONTRIBUTING.md, QUICKSTART.md) — verified against GitHub
- Click 8.3 documentation — verified against official docs
- httpx 0.28.1 — verified against PyPI

### Secondary (MEDIUM confidence)
- FroeMic/attio-cli — community project, used for gap analysis
- clig.dev — CLI design reference
- Agent CLI design guides — multiple community sources

---
*Research completed: 2026-03-30*
*Ready for roadmap: yes*
