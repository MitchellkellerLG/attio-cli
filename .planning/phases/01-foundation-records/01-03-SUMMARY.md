---
phase: 01-foundation-records
plan: "03"
subsystem: formatter
tags: [formatter, output, rich, json, tty, stderr]
dependency_graph:
  requires: [01-01]
  provides: [format_output, format_error, format_pagination_footer]
  affects: [01-05-records, 01-06-cli-entry]
tech_stack:
  added: []
  patterns: [TTY-aware output, Rich table rendering, stderr-only errors]
key_files:
  created: []
  modified:
    - agent-harness/cli_anything/attio/utils/formatter.py
    - agent-harness/cli_anything/attio/tests/test_formatter.py
decisions:
  - "format_output() is the ONLY function that calls json.dumps or print — all commands route through it"
  - "TTY detection via sys.stdout.isatty() — piped output auto-falls back to JSON (D-13)"
  - "Rich Console(stderr=True) for errors — stdout is always clean data only"
metrics:
  duration: 2 minutes
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_modified: 2
requirements:
  - INFRA-08
  - INFRA-09
  - INFRA-10
---

# Phase 01 Plan 03: Output Formatter Summary

**One-liner:** TTY-aware formatter with Rich tables on terminal, JSON when piped, and stderr-only error routing — single entry point for all CLI output.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | formatter.py — format_output, format_error, format_pagination_footer | 2dd8c52 | agent-harness/cli_anything/attio/utils/formatter.py |
| 2 | test_formatter.py — 8 unit tests covering all formatter behaviors | 2dd8c52 | agent-harness/cli_anything/attio/tests/test_formatter.py |

## What Was Built

`formatter.py` is the single output gateway for the entire CLI. No command will ever call `json.dumps`, `print`, or `console.print` directly — everything routes through these three functions:

- **`format_output(data, as_json, stream, object_type)`** — The main dispatch. `as_json=True` or piped stdout → `json.dumps` via `click.echo`. TTY → Rich table with object-type-specific columns.
- **`format_error(message, hint)`** — Always writes to stderr via `Console(stderr=True)`. Optional hint line for actionable guidance (D-10 pattern).
- **`format_pagination_footer(count, has_more, as_json)`** — D-15 implementation. Terminal mode: human footer with `--all` instruction. JSON mode: `{"count": N, "has_more": true}` structured output.

**`_DEFAULT_COLUMNS`** defines table columns per object type:
- people: name, email_addresses, phone_numbers
- companies: name, domains
- deals: name, stage, value
- users: name, email_addresses
- workspaces: name, domains
- unknown types: first 3 keys from record values

**`_extract_display_value()`** handles Attio's multi-value attribute arrays — tries `value`, `email_address`, `phone_number`, `domain`, `original_value` in priority order.

## Test Results

```
8 passed in 0.02s
```

All 8 tests pass:
- `TestJsonOutput`: json flag forces json, piped output is json, list output works
- `TestErrorOutput`: error to stderr, hint appears in stderr, stdout stays clean
- `TestPaginationFooter`: footer in terminal mode, json mode, no footer when no_more=False

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All three exported functions are fully implemented and tested.

## Self-Check: PASSED

- [x] `agent-harness/cli_anything/attio/utils/formatter.py` exists with `format_output`, `format_error`, `format_pagination_footer`
- [x] `agent-harness/cli_anything/attio/tests/test_formatter.py` exists with 8 passing tests
- [x] Commit 2dd8c52 exists
- [x] Import verify exits 0 with "formatter imports OK"
