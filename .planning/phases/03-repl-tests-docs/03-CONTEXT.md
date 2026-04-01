# Phase 3 Context: REPL, Tests, and Docs

**Phase**: 3 — REPL, Tests, and Docs
**Goal**: The CLI has an interactive REPL, a passing test suite, and documentation that makes it agent-discoverable
**Depends on**: Phase 2 (complete)

## Requirements

- REPL-01: `attio repl` — interactive session with persistent context
- REPL-02: REPL history saved to `~/.config/attio/history` (arrow-up)
- REPL-03: Tab completion of commands and subcommands inside REPL
- REPL-04: REPL continues on command errors (shows error, returns to prompt — no crash)
- REPL-05: `--yes` flag suppresses all confirmation prompts (non-interactive/agent use)
- TEST-01: Unit tests for AttioClient (auth, rate limiting, pagination, retry)
- TEST-02: Unit tests for all command groups (Click CliRunner)
- TEST-03: Unit tests for formatter (JSON output, table rendering)
- TEST-04: E2E tests against live Attio API (LeadGrow workspace)
- TEST-05: CI-ready test suite (no real API calls in unit tests via pytest-httpx)
- DOC-01: SKILL.md for AI agent discovery
- DOC-02: ATTIO.md SOP document with usage examples
- DOC-03: setup.py with entry_points for `cli-anything-attio` command

## Success Criteria

1. `attio repl` starts with arrow-key history, tab completion, graceful error recovery (no crash on bad command)
2. `--yes` flag suppresses all confirmation prompts for non-interactive/agent use
3. `pytest` passes all unit tests with no real API calls (pytest-httpx mocks); E2E tests against LeadGrow workspace pass
4. SKILL.md exists and is loadable for AI agent discovery; ATTIO.md SOP with usage examples
5. `pip install -e .` registers the `cli-anything-attio` entry point and CLI is usable as a package

## Current State

**Built (Phase 1+2):**
- 20 CLI command groups registered in `attio_cli.py`
- Modules: records, notes, tasks, comments, threads, lists, entries, objects, attributes, files, meetings, webhooks, workspace, config
- Utils: attio_client.py, config.py, exceptions.py, formatter.py, pagination.py
- Test files exist for every module (conftest.py has full mock fixtures)
- setup.py already has `cli-anything-attio` entry point via `cli_anything.attio.attio_cli:cli`
- pyproject.toml configured for pytest (testpaths, addopts)

**NOT yet built:**
- `repl.py` — REPL module (click-repl + prompt-toolkit)
- `--yes` flag on destructive commands (delete operations)
- `test_e2e.py` is empty — E2E tests needed
- `SKILL.md` — agent discovery document
- `ATTIO.md` — SOP document
- `attio` short alias entry point (currently only `cli-anything-attio`)

## Tech Stack

- **click-repl 0.3.0** — bridges Click command tree into prompt-toolkit's interactive loop
- **prompt-toolkit 3.0.52** — already installed (history, completion, key bindings)
- **click 8.3.1** — CLI framework (already installed)
- Config path for history: `~/.config/attio/history`
- History file uses prompt-toolkit's `FileHistory`

## Key Constraints

- `--yes` flag should be added to: delete commands across all modules (records, notes, tasks, comments, entries, files, webhooks)
- REPL must NOT crash on unknown commands — catch exceptions, print error, resume prompt
- E2E tests must be skipped by default (require `ATTIO_API_KEY` env var set)
- Unit tests use `pytest-httpx` for HTTP mocking (no real API calls)
- SKILL.md format follows CLI-Anything convention: commands table, auth setup, agent usage patterns

## Known Blockers (from STATE.md)

- pytest-httpx 0.35+ compatibility with httpx 0.28.1 — verify before first test run
- CLI-Anything undo/redo scaffolding — out of scope for Phase 3 (v2 requirement)
- Attio `--dry-run` — client-side only, no API header support (v2 requirement)

## File Locations

- CLI entry: `agent-harness/cli_anything/attio/attio_cli.py`
- New REPL module: `agent-harness/cli_anything/attio/repl.py`
- Tests: `agent-harness/cli_anything/attio/tests/`
- E2E tests: `agent-harness/cli_anything/attio/tests/test_e2e.py`
- REPL tests: `agent-harness/cli_anything/attio/tests/test_repl.py`
- Docs: `agent-harness/cli_anything/attio/` (SKILL.md, ATTIO.md)
- Package config: `setup.py`, `pyproject.toml`
