---
phase: 03
plan: 02
title: Test Suite Audit and E2E Tests
status: complete
completed: 2026-03-31
commit: 00b1a2d
---

# Phase 03 Plan 02: Test Suite Audit and E2E Tests — Summary

**One-liner:** Fixed CliRunner fixture breaking all 172 tests, filled test_e2e.py with 5 guarded E2E tests that skip without ATTIO_API_KEY.

## Status: Complete

## Baseline Test Audit (Task 1)

**Before fix:**
- 73 passed, 172 errors
- Root cause: single fixture issue — `CliRunner(mix_stderr=False)` in `conftest.py` line 188
- `mix_stderr` parameter was removed from Click 8.x `CliRunner.__init__`
- All 172 errors were identical fixture setup failures — no import errors, no assertion failures
- test_repl.py did not exist yet (03-01 running in parallel — expected)

## Fixes Applied (Task 2)

**[Rule 1 - Bug] Removed unsupported `mix_stderr=False` from CliRunner fixture**

- **Found during:** Task 1 baseline audit
- **Issue:** `CliRunner(mix_stderr=False)` raises `TypeError` in Click 8.x — `mix_stderr` was removed
- **Fix:** Changed `return CliRunner(mix_stderr=False)` to `return CliRunner()` in conftest.py
- **Files modified:** `agent-harness/cli_anything/attio/tests/conftest.py`
- **Result:** 172 errors → 0 errors, 73 → 245 tests passing

## Final Test Counts

| Category | Count | Status |
|---|---|---|
| Unit tests (excl. test_repl.py) | 245 | PASSED |
| E2E tests | 5 | SKIPPED (ATTIO_API_KEY not set) |
| test_repl.py | 4 | FAILED (03-01 scope — expected) |

**Exit code (excl. test_repl.py):** 0

## E2E Test Coverage (Task 3)

File: `agent-harness/cli_anything/attio/tests/test_e2e.py`

| Class | Test | Endpoint |
|---|---|---|
| TestE2EWorkspace | test_workspace_self_returns_json | GET /v2/self |
| TestE2EWorkspace | test_workspace_members_returns_list | GET /v2/workspace/members |
| TestE2EPeople | test_people_list_returns_records | GET /v2/objects/people/records |
| TestE2ENotes | test_notes_list_returns_json | GET /v2/notes |
| TestE2ETasks | test_tasks_list_returns_json | GET /v2/tasks |

Guard pattern: `pytestmark = pytest.mark.skipif(not os.getenv("ATTIO_API_KEY"), reason="...")`

## Verification Results (Task 4)

```
245 passed, 5 skipped in 10.82s
Exit code: 0
```

All E2E tests appear as `s` (skipped), not `F` or `E`. Zero unit test failures or errors.

## Deviations from Plan

**[Rule 1 - Bug] Fixed CliRunner mix_stderr incompatibility**
- Found during mandatory Task 1 baseline run
- `mix_stderr` removed from Click 8.x CliRunner — not an optional cleanup, a hard blocker
- Single-line fix, zero test rewrites
- Commit: 00b1a2d

## Self-Check

- [x] `agent-harness/cli_anything/attio/tests/test_e2e.py` — written and verified
- [x] `agent-harness/cli_anything/attio/tests/conftest.py` — fix confirmed working
- [x] Commit 00b1a2d exists in git log
- [x] 245 unit tests pass, exit code 0 confirmed
- [x] 5 E2E tests skip cleanly on missing ATTIO_API_KEY

## Self-Check: PASSED
