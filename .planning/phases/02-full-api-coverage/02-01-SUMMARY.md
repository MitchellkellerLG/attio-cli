---
phase: 02-full-api-coverage
plan: "01"
subsystem: notes-tasks
tags: [notes, tasks, crud, cli-commands, attio-api]
dependency_graph:
  requires: [01-foundation-records]
  provides: [notes-commands, tasks-commands]
  affects: [attio_cli.py, attio_client.py]
tech_stack:
  added: []
  patterns: [records.py-canonical-pattern, click-group-factory, create_autospec-mock]
key_files:
  created:
    - agent-harness/cli_anything/attio/notes.py
    - agent-harness/cli_anything/attio/tasks.py
    - agent-harness/cli_anything/attio/tests/test_notes.py
    - agent-harness/cli_anything/attio/tests/test_tasks.py
  modified:
    - agent-harness/cli_anything/attio/utils/attio_client.py
    - agent-harness/cli_anything/attio/tests/conftest.py
    - agent-harness/cli_anything/attio/attio_cli.py
decisions:
  - notes_group and tasks_group registered in attio_cli.py using same add_command pattern as existing groups
  - tasks --completed/--not-completed uses Click flag pair (default=None) to allow unset state for list filtering
  - tasks update uses same --completed/--not-completed pair for consistency with list
  - assignees and linked-records in tasks create accept repeatable --assignee/--linked-record JSON strings
metrics:
  duration_seconds: 784
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_modified: 7
---

# Phase 02 Plan 01: Notes and Tasks CLI Commands Summary

**One-liner:** Notes and tasks CRUD commands with 10 new AttioClient methods, 34 passing tests, and full CLI registration following the records.py canonical pattern.

## What Was Built

Full CRUD command groups for Attio's notes and tasks resources:

- **notes_group** (5 commands): create, get, list, update, delete
- **tasks_group** (5 commands): create, get, list, update, delete
- **10 new AttioClient methods** (5 notes + 5 tasks) appended to attio_client.py
- **34 tests** across test_notes.py (15) and test_tasks.py (19), all passing
- **SAMPLE_NOTE and SAMPLE_TASK** canned responses added to conftest.py with full mock_client wiring
- Both groups registered in attio_cli.py

## Deviations from Plan

None — plan executed exactly as written.

The only noteworthy implementation choice: Task 1 and Task 2 were committed as a single atomic commit because Task 1 tests require the CLI registration from Task 2 to run at all (exit code 2 = "no such command" without registration). Logically separating them would produce a broken intermediate state. The commit message documents both tasks.

## Test Results

```
34 passed in 0.34s
```

All 5 test classes per module:
- TestNotesCreate, TestNotesGet, TestNotesList, TestNotesUpdate, TestNotesDelete
- TestTasksCreate, TestTasksGet, TestTasksList, TestTasksUpdate, TestTasksDelete

## Key Acceptance Criteria Verified

- `create_note` in attio_client.py: 1 match
- `create_task` in attio_client.py: 1 match
- `list_notes` in attio_client.py: 1 match
- `list_tasks` in attio_client.py: 1 match
- `notes_group` in notes.py: 6 matches
- `tasks_group` in tasks.py: 6 matches
- `SAMPLE_NOTE` in conftest.py: 5 matches
- `SAMPLE_TASK` in conftest.py: 5 matches
- CLI command list includes "notes" and "tasks"

## Known Stubs

None.

## Self-Check: PASSED
