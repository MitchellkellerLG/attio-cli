---
phase: 01-foundation-records
plan: "01"
subsystem: infra
tags: [python, click, httpx, pytest, ruff, mypy, cli-anything, setuptools]

# Dependency graph
requires: []
provides:
  - agent-harness/cli_anything/attio/ directory layout with all module stubs
  - setup.py with cli-anything-attio console_scripts entry point
  - pyproject.toml with ruff + mypy + pytest config
  - conftest.py with CliRunner, mock_client, sample_person, sample_company fixtures
  - .env.example and .gitignore
affects: [01-02, 01-03, 01-04, 01-05, 01-06]

# Tech tracking
tech-stack:
  added: [click>=8.3.1, httpx>=0.28.1, tenacity>=9.1.4, rich>=14.3.3, python-dotenv>=1.2.2, prompt-toolkit>=3.0.52, rich-click>=1.9, pytest>=7.0, pytest-httpx>=0.35, ruff, mypy]
  patterns:
    - "CLI-Anything directory layout: agent-harness/cli_anything/attio/ with utils/ and tests/ subdirs"
    - "setup.py package_dir pointing to agent-harness/ for installable package"
    - "pyproject.toml as single config source for ruff + mypy + pytest"
    - "conftest.py canned API responses as module-level dicts, fixtures return them"

key-files:
  created:
    - setup.py
    - pyproject.toml
    - .env.example
    - .gitignore
    - agent-harness/cli_anything/__init__.py
    - agent-harness/cli_anything/attio/__init__.py
    - agent-harness/cli_anything/attio/attio_cli.py
    - agent-harness/cli_anything/attio/records.py
    - agent-harness/cli_anything/attio/utils/__init__.py
    - agent-harness/cli_anything/attio/utils/config.py
    - agent-harness/cli_anything/attio/utils/attio_client.py
    - agent-harness/cli_anything/attio/utils/formatter.py
    - agent-harness/cli_anything/attio/utils/pagination.py
    - agent-harness/cli_anything/attio/utils/exceptions.py
    - agent-harness/cli_anything/attio/tests/__init__.py
    - agent-harness/cli_anything/attio/tests/conftest.py
    - agent-harness/cli_anything/attio/tests/test_client.py
    - agent-harness/cli_anything/attio/tests/test_commands.py
    - agent-harness/cli_anything/attio/tests/test_formatter.py
    - agent-harness/cli_anything/attio/tests/test_e2e.py
  modified: []

key-decisions:
  - "package_dir points to agent-harness/ so all CLI-Anything packages install from there"
  - "pyproject.toml is the single config file for all dev tools (ruff, mypy, pytest)"
  - "conftest.py canned responses modeled on real Attio API response shapes (id.record_id, values dict)"

patterns-established:
  - "Module stubs contain only a docstring — no placeholder functions"
  - "conftest.py defines all shared fixtures; individual test files import nothing from conftest (pytest auto-loads it)"
  - "CliRunner initialized with mix_stderr=False to enable separate stderr assertions"

requirements-completed: [INFRA-12, INFRA-13]

# Metrics
duration: 2min
completed: 2026-03-31
---

# Phase 01 Plan 01: Project Scaffold Summary

**Python package scaffold with CLI-Anything directory layout, installable setup.py, ruff/mypy/pytest config, and conftest.py fixtures matching real Attio API response shapes**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-31T13:26:21Z
- **Completed:** 2026-03-31T13:28:15Z
- **Tasks:** 2
- **Files modified:** 20

## Accomplishments

- Full CLI-Anything directory layout under agent-harness/cli_anything/attio/ with utils/ and tests/ subdirs
- Installable package via setup.py with console_scripts entry pointing to attio_cli:cli
- Single pyproject.toml config for ruff, mypy, and pytest — no separate config files
- conftest.py with CliRunner, pre-wired mock_client, and canned API response fixtures that match real Attio v2 shapes

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold — directories, stubs, setup.py, pyproject.toml** - `38f8b84` (chore)
2. **Task 2: conftest.py — shared test fixtures** - `179a14a` (feat)

## Files Created/Modified

- `setup.py` - Package config with cli-anything-attio console_scripts entry point
- `pyproject.toml` - ruff + mypy + pytest unified config
- `.env.example` - ATTIO_API_KEY placeholder
- `.gitignore` - Standard Python ignores including .venv, .env, __pycache__
- `agent-harness/cli_anything/__init__.py` - CLI-Anything plugin package stub
- `agent-harness/cli_anything/attio/__init__.py` - Attio plugin stub
- `agent-harness/cli_anything/attio/attio_cli.py` - CLI entry point stub
- `agent-harness/cli_anything/attio/records.py` - Records command groups stub
- `agent-harness/cli_anything/attio/utils/{__init__,config,attio_client,formatter,pagination,exceptions}.py` - Utility stubs
- `agent-harness/cli_anything/attio/tests/conftest.py` - Shared fixtures with canned Attio API responses
- `agent-harness/cli_anything/attio/tests/{__init__,test_client,test_commands,test_formatter,test_e2e}.py` - Test stubs

## Decisions Made

- `package_dir={"": "agent-harness"}` in setup.py so the installable package root is inside agent-harness/, following CLI-Anything convention
- pyproject.toml serves as single config source — no separate .ruff.toml, setup.cfg, or pytest.ini
- conftest.py canned responses use real Attio v2 shapes (nested `id.record_id`, `values` dict with attribute arrays) so tests stay realistic without hitting the API

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- `python` and `python3` not in PATH on this Windows environment. Used `/c/Windows/py -3` (Python Launcher for Windows) for pytest verification. Python 3.11.3 detected. Not a blocker — pytest collected 0 items (correct for stub-only files) with exit code 5 (no tests collected), which is expected at scaffold stage.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All module stubs in place — Plans 02-05 can populate them without directory changes
- conftest.py fixtures ready — test files can import and use mock_client, runner, sample_person immediately
- setup.py entry point wired — once attio_cli.py has a `cli` Click group, the package installs and runs
- Potential concern: pytest-httpx 0.35+ / httpx 0.28.1 compatibility (noted in STATE.md blockers) — verify before Plan 04 first test run

---
*Phase: 01-foundation-records*
*Completed: 2026-03-31*
