---
phase: 02-full-api-coverage
plan: "06"
subsystem: attio-cli
tags: [webhooks, workspace, cli, full-api-coverage, wave-2]
dependency_graph:
  requires: [02-01, 02-02, 02-03, 02-04, 02-05]
  provides: [webhooks-commands, workspace-commands, full-api-coverage]
  affects: [attio_cli.py, attio_client.py]
tech_stack:
  added: []
  patterns:
    - "click.Group with CRUD commands (create/get/list/update/delete) for webhooks"
    - "read-only click.Group (members/member/self) for workspace"
    - "JSON parse + ClickException for --subscriptions and --data options"
    - "self_check() reused for workspace self command"
key_files:
  created:
    - agent-harness/cli_anything/attio/webhooks.py
    - agent-harness/cli_anything/attio/workspace.py
    - agent-harness/cli_anything/attio/tests/test_webhooks.py
    - agent-harness/cli_anything/attio/tests/test_workspace.py
  modified:
    - agent-harness/cli_anything/attio/utils/attio_client.py
    - agent-harness/cli_anything/attio/tests/conftest.py
    - agent-harness/cli_anything/attio/attio_cli.py
decisions:
  - "attio_cli.py registration done in same commit as Task 1 because test verification requires it — tests invoke cli routes that need webhooks_group and workspace_group registered"
  - "self_check() reused for workspace self command as planned — no new method needed"
  - "20 top-level commands in CLI (exceeds 19 minimum — threads is a separate top-level group alongside comments)"
metrics:
  duration_seconds: 186
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_changed: 7
---

# Phase 2 Plan 06: Webhooks + Workspace Commands Summary

Webhooks CRUD and workspace members CLI added. Full test suite passes at 245 tests across all command groups. Complete Attio API coverage achieved.

## What Was Built

**7 new AttioClient methods:**
- `create_webhook(target_url, subscriptions)` — POST /webhooks
- `get_webhook(webhook_id)` — GET /webhooks/{id}
- `list_webhooks()` — GET /webhooks
- `update_webhook(webhook_id, data)` — PATCH /webhooks/{id}
- `delete_webhook(webhook_id)` — DELETE /webhooks/{id}
- `list_workspace_members()` — GET /workspace-members
- `get_workspace_member(member_id)` — GET /workspace-members/{id}

**webhooks.py** — 5 commands: `create`, `get`, `list`, `update`, `delete`
- `create` takes `--target-url` and `--subscriptions` (JSON array), validates JSON before calling client
- `update` takes `--data` (JSON object), flexible update for any webhook field
- `delete` has `--yes` skip-confirmation flag

**workspace.py** — 3 read-only commands: `members`, `member`, `self`
- `self` reuses `client.self_check()` — same endpoint as auth validation, no new client method needed

**conftest.py** — Added `SAMPLE_WEBHOOK`, `SAMPLE_WORKSPACE_MEMBER`, and wired 7 new mock returns into `mock_client` fixture.

**attio_cli.py** — Added imports and `cli.add_command` calls for `webhooks_group` and `workspace_group`. Final count: 20 top-level commands.

## Test Results

- **New tests:** 29 (19 webhooks + 10 workspace)
- **Full suite:** 245 passed, 0 failed
- **Previous baseline:** 216 tests (all still passing)
- Tests cover: client call assertions, JSON output validation, error handling (invalid JSON), confirmation prompts, read-only verification

## Deviations from Plan

**1. [Rule 3 - Blocking] Task 1 verification required attio_cli.py registration**

- **Found during:** Task 1 test run
- **Issue:** test_webhooks.py and test_workspace.py import `cli` from attio_cli.py and invoke `webhooks` / `workspace` subcommands. These commands return exit code 2 (no such command) until registered.
- **Fix:** Included attio_cli.py registration changes (imports + add_command calls) in the Task 1 commit rather than Task 2. Task 2 became full-suite verification only.
- **Files modified:** agent-harness/cli_anything/attio/attio_cli.py
- **Commit:** 9607bb8

## Known Stubs

None. All commands wire to real AttioClient methods. No placeholder data in output paths.

## Self-Check

Checking created files exist and commits are present.
