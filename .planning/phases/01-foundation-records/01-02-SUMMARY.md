---
phase: 01-foundation-records
plan: "02"
subsystem: utils
tags: [config, exceptions, auth, exit-codes, xdg]
dependency_graph:
  requires: ["01-01"]
  provides: ["01-03", "01-04", "01-05"]
  affects: ["all plans in phase 01"]
tech_stack:
  added: [python-dotenv]
  patterns: [XDG config, semantic exit codes, click.ClickException hierarchy, stderr-only errors]
key_files:
  created:
    - agent-harness/cli_anything/attio/utils/exceptions.py
    - agent-harness/cli_anything/attio/utils/config.py
    - agent-harness/cli_anything/attio/tests/test_exceptions.py
    - agent-harness/cli_anything/attio/tests/test_config.py
  modified: []
decisions:
  - "exceptions.py implemented before config.py because config imports AuthError — write order matters for TDD clarity"
  - "save_config omits base_url key entirely when not provided (dict stays minimal)"
  - "Malformed config JSON falls through silently to AuthError rather than surfacing JSONDecodeError"
metrics:
  duration_minutes: 15
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_changed: 4
---

# Phase 01 Plan 02: Config + Exceptions Summary

**One-liner:** XDG config loading (env var + file fallback) and semantic exit code exception hierarchy using click.ClickException, with AuthError on missing key and stderr-only error output.

## What Was Built

Two foundational utility modules that every downstream plan imports:

**exceptions.py** — Full exception hierarchy inheriting `click.ClickException`:
- `AttioError` base: configurable `exit_code`, optional `hint`, stderr-only `show()`
- `AuthError(exit_code=4)` — default message + hint pointing to `attio config set api-key`
- `NotFoundError(exit_code=3)` — resource identifier in message
- `RateLimitError(exit_code=5)` — stores `retry_after` float
- `TransientError(exit_code=1)` — stores `status_code` int
- Authorization bearer value never appears in any message, repr, or hint

**config.py** — Auth config loading and persistence:
- `AttioConfig` dataclass: `api_key: str`, `base_url: str = "https://api.attio.com/v2"`
- `load_config()` — `ATTIO_API_KEY` env var takes precedence (D-08); falls back to `~/.config/attio/config.json` (D-07); raises `AuthError` with actionable hint if key absent
- `save_config()` — writes XDG config, `chmod 0o600` for owner-read security
- Module-level constants: `CONFIG_DIR`, `CONFIG_FILE`, `HISTORY_FILE`
- `python-dotenv` loads `.env` on import

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| Task 2 | exceptions.py — semantic exception hierarchy | 57c2fb5 |
| Task 1 | config.py — env var + XDG config loading | 2d6dde1 |

Note: Task 2 was implemented before Task 1 since config.py imports from exceptions.py.

## Test Coverage

47 tests across two new test files:
- `test_exceptions.py` — 27 tests covering all exception classes, hierarchy, stderr behavior, no-bearer-token invariant
- `test_config.py` — 20 tests covering env var, file fallback, precedence, malformed JSON, save with chmod, all constants

All 47 pass.

## Verification

```
All imports OK
CONFIG_DIR: C:\Users\mitch\.config\attio
```

## Deviations from Plan

None — plan executed exactly as written. Task 2 (exceptions) was implemented before Task 1 (config) due to import dependency, which matches the plan's note in Task 1's `read_first` list.

## Known Stubs

None — both modules are fully implemented with no placeholder values or TODOs.

## Self-Check: PASSED
