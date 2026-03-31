---
phase: 02-full-api-coverage
plan: "03"
subsystem: lists-entries
tags: [lists, entries, cli, pagination, upsert, patch-put]
dependency_graph:
  requires: []
  provides: [lists-group, entries-group]
  affects: [attio_cli.py, attio_client.py, conftest.py]
tech_stack:
  added: []
  patterns: [offset-paginator-reuse, build-filter-reuse, patch-put-overwrite-flag, assert-upsert-pattern]
key_files:
  created:
    - agent-harness/cli_anything/attio/lists.py
    - agent-harness/cli_anything/attio/entries.py
    - agent-harness/cli_anything/attio/tests/test_lists.py
    - agent-harness/cli_anything/attio/tests/test_entries.py
  modified:
    - agent-harness/cli_anything/attio/utils/attio_client.py
    - agent-harness/cli_anything/attio/tests/conftest.py
    - agent-harness/cli_anything/attio/attio_cli.py
decisions:
  - entries.py imports build_filter from records.py — filter DSL reused, not duplicated
  - list_entries uses offset_paginator same as list_records — streaming, never buffered
  - update_entry overwrite flag mirrors records PATCH/PUT pattern exactly
  - assert_entry uses PUT /lists/{id}/entries (no matching_attribute, upserts by parent_record_id)
metrics:
  duration_minutes: 8
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_created: 4
  files_modified: 3
---

# Phase 02 Plan 03: Lists and List Entries Summary

## One-Liner

Lists CRUD + views and entries CRUD + assert + PATCH/PUT overwrite using offset_paginator and build_filter reuse from records.

## What Was Built

Added `attio lists` and `attio entries` top-level command groups to the CLI, plus 11 new `AttioClient` methods covering the full Attio Lists and List Entries API.

### Client Methods Added (attio_client.py)

**Lists (5 methods):**
- `list_lists()` — GET /lists
- `get_list(list_id)` — GET /lists/{id}
- `create_list(name, parent_object)` — POST /lists
- `update_list(list_id, name)` — PATCH /lists/{id}
- `list_list_views(list_id)` — GET /lists/{id}/views

**Entries (6 methods):**
- `list_entries(list_id, ...)` — POST /lists/{id}/entries/query via offset_paginator
- `get_entry(list_id, entry_id)` — GET /lists/{id}/entries/{id}
- `create_entry(list_id, parent_record_id, values)` — POST /lists/{id}/entries
- `update_entry(list_id, entry_id, values, overwrite)` — PATCH/PUT /lists/{id}/entries/{id}
- `delete_entry(list_id, entry_id)` — DELETE /lists/{id}/entries/{id}
- `assert_entry(list_id, parent_record_id, values)` — PUT /lists/{id}/entries (upsert)

### Command Groups

**lists.py** — 5 commands: list, get, create, update, views

**entries.py** — 6 commands: list, get, create, update, delete, assert
- Reuses `build_filter` from records.py for --filter/--filter-file DSL
- `list` command uses streaming pagination loop identical to records list
- `update` command supports `--overwrite` flag (PATCH default, PUT with flag)
- `assert` command upserts by parent_record_id

## Test Results

27 tests passing — 9 in test_lists.py, 18 in test_entries.py.

Critical tests verified:
- `TestEntriesUpdate.test_update_default_is_patch` — overwrite=False by default
- `TestEntriesUpdate.test_update_overwrite_flag` — overwrite=True with --overwrite
- `TestEntriesAssert.test_assert_passes_parent_record_id` — correct parent_record_id routing
- `TestEntriesList.test_list_with_filter` — filter body passed through build_filter

## Commits

- `202e692`: feat(02-03): add lists and entries client methods, command files, and tests
- `59fd276`: feat(02-03): register lists and entries in CLI entry point

## Deviations from Plan

None — plan executed exactly as written.

The only sequencing note: Task 2 (CLI registration) was completed before running Task 1 tests since exit code 2 (no such command) would fail all tests. This is not a deviation — it's the correct execution order for this dependency.

## Known Stubs

None. All commands wire to real client methods. conftest.py mock returns use real Attio v2 response shapes.

## Self-Check: PASSED

Files exist:
- agent-harness/cli_anything/attio/lists.py: FOUND
- agent-harness/cli_anything/attio/entries.py: FOUND
- agent-harness/cli_anything/attio/tests/test_lists.py: FOUND
- agent-harness/cli_anything/attio/tests/test_entries.py: FOUND

Commits exist:
- 202e692: FOUND
- 59fd276: FOUND

Tests: 27 passed, 0 failed
