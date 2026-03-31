# Phase 3: REPL, Tests, and Docs — Research

**Researched:** 2026-03-31
**Domain:** click-repl 0.3.0, prompt-toolkit 3.0.52, pytest-httpx 0.36, Click CliRunner, CLI-Anything SKILL.md format
**Confidence:** HIGH

---

## Summary

Phase 3 is a well-defined build: a REPL module, filling in test gaps, and writing two documentation files. The hard research questions were about click-repl's exact API and how to test a REPL without a terminal. Both are answered definitively.

The `--yes` flag is already implemented on all delete commands in all modules (records, notes, tasks, comments, entries, files, webhooks). This is done — no new code required for REPL-05.

pytest-httpx 0.36.0 is installed on the system (global Python 3.11 env). The test suite in `test_client.py` already imports and uses `HTTPXMock` successfully against httpx 0.28.1. Compatibility is confirmed.

The REPL must be implemented as a custom `repl.py` module that calls `click_repl.repl()` directly (not `register_repl`) so it can pass `prompt_kwargs` with `FileHistory`. REPL testing uses `mock_stdin` (not CliRunner) — the REPL function uses `sys.stdin.readline()` in non-TTY mode, making it testable without a terminal.

**Primary recommendation:** Wire the REPL manually (not via `register_repl`) to control `prompt_kwargs`, exception handling, and history path. Test it by patching `sys.stdin` with `io.StringIO`. Write SKILL.md following the commands-table format seen in `.claude/skills/` examples.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- click-repl 0.3.0 bridges Click command tree into prompt-toolkit's interactive loop
- prompt-toolkit 3.0.52 for history, completion, key bindings
- History file path: `~/.config/attio/history`
- History implementation: `prompt_toolkit.history.FileHistory`
- `--yes` flag on: delete commands across records, notes, tasks, comments, entries, files, webhooks
- REPL must NOT crash on unknown commands — catch exceptions, print error, resume prompt
- E2E tests must be skipped by default (require `ATTIO_API_KEY` env var set)
- Unit tests use `pytest-httpx` for HTTP mocking (no real API calls)
- SKILL.md format follows CLI-Anything convention: commands table, auth setup, agent usage patterns
- setup.py must add `attio` short alias entry point alongside `cli-anything-attio`
- New REPL module at: `agent-harness/cli_anything/attio/repl.py`
- Docs at: `agent-harness/cli_anything/attio/` (SKILL.md, ATTIO.md)

### Claude's Discretion
- REPL prompt string (e.g., `"attio> "`)
- SKILL.md content depth — commands table is mandatory, detail beyond that is judgment
- ATTIO.md SOP structure and length
- E2E test selection (which endpoints to cover against LeadGrow workspace)
- How to create the `~/.config/attio/` directory if it doesn't exist before opening FileHistory

### Deferred Ideas (OUT OF SCOPE)
- CLI-Anything undo/redo scaffolding (v2 requirement)
- Attio `--dry-run` API header (v2 requirement — client-side only simulation not required)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REPL-01 | `attio repl` — interactive session with persistent context | click_repl.repl() called from a custom `repl` command registered on `cli` group |
| REPL-02 | REPL history saved to `~/.config/attio/history` (arrow-up) | `FileHistory(str(Path.home() / ".config/attio/history"))` passed via `prompt_kwargs["history"]` |
| REPL-03 | Tab completion of commands and subcommands inside REPL | Built into click-repl's `ClickCompleter` — included automatically via `bootstrap_prompt()` |
| REPL-04 | REPL continues on command errors (shows error, returns to prompt — no crash) | click-repl already catches `click.ClickException`, `SystemExit`, `ClickExit`; add broad `Exception` catch for unexpected errors |
| REPL-05 | `--yes` flag suppresses all confirmation prompts | Already implemented on all delete commands — verified in records, notes, tasks, comments, entries, files, webhooks |
| TEST-01 | Unit tests for AttioClient (auth, rate limiting, pagination, retry) | test_client.py already exists with HTTPXMock patterns — fill gaps if any |
| TEST-02 | Unit tests for all command groups (Click CliRunner) | test_commands.py pattern established — remaining command modules need coverage |
| TEST-03 | Unit tests for formatter (JSON output, table rendering) | test_formatter.py exists — verify coverage |
| TEST-04 | E2E tests against live Attio API (LeadGrow workspace) | test_e2e.py is empty — implement with `pytest.mark.skipif(not os.getenv("ATTIO_API_KEY"), ...)` |
| TEST-05 | CI-ready test suite (no real API calls in unit tests via pytest-httpx) | pytest-httpx 0.36.0 + httpx 0.28.1 confirmed compatible — existing test_client.py proves it |
| DOC-01 | SKILL.md for AI agent discovery | Commands table + YAML frontmatter + auth setup + agent usage patterns |
| DOC-02 | ATTIO.md SOP document with usage examples | SOP format with install, auth, command reference, and agent workflow examples |
| DOC-03 | setup.py with entry_points for `cli-anything-attio` command | Already exists; add `attio=cli_anything.attio.attio_cli:cli` short alias entry |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click-repl | 0.3.0 | Wire Click group into prompt-toolkit REPL loop | CLI-Anything hard requirement; provides ClickCompleter, history, `!` shell escapes, `:help` meta-commands |
| prompt-toolkit | 3.0.52 | History persistence, completion, key bindings | Already installed as dependency; FileHistory for persistent history |
| pytest-httpx | 0.36.0 | Mock httpx in unit tests | Already installed (global Python 3.11); HTTPXMock fixture pattern established in test_client.py |
| Click CliRunner | 8.3.1 | Test command invocation without terminal | Already in use in test_commands.py; mock sys.stdin for REPL tests |

### REPL Implementation Notes
click-repl 0.3.0 is not installed in the attio-cli virtual environment yet (not in setup.py `install_requires`). It must be added.

**Installation:**
```bash
# Add to setup.py install_requires:
"click-repl>=0.3.0",

# Then reinstall:
pip install -e ".[dev]"
```

---

## Architecture Patterns

### Pattern 1: REPL Module Structure

The REPL should NOT use `register_repl(cli)` because that registers `repl` as a simple passthrough with no ability to inject `prompt_kwargs`. Instead, write a custom `@cli.command()` that calls `click_repl.repl()` directly.

```python
# agent-harness/cli_anything/attio/repl.py
import os
from pathlib import Path

import click
from click_repl import repl as click_repl_run
from prompt_toolkit.history import FileHistory


def get_history_path() -> str:
    history_dir = Path.home() / ".config" / "attio"
    history_dir.mkdir(parents=True, exist_ok=True)
    return str(history_dir / "history")


def register_repl_command(cli_group: click.Group) -> None:
    """Register the `repl` subcommand on the given Click group."""

    @cli_group.command("repl")
    @click.pass_context
    def repl_cmd(ctx: click.Context) -> None:
        """Start an interactive REPL session.

        Arrow-up history, tab completion, graceful error recovery.
        Type :help for meta-commands, :quit or Ctrl-D to exit.
        """
        prompt_kwargs = {
            "history": FileHistory(get_history_path()),
            "message": "attio> ",
        }
        click_repl_run(ctx, prompt_kwargs=prompt_kwargs)
```

Register it in `attio_cli.py`:
```python
from .repl import register_repl_command
# At bottom of attio_cli.py, after all cli.add_command() calls:
register_repl_command(cli)
```

### Pattern 2: How bootstrap_prompt() Merges prompt_kwargs

`bootstrap_prompt()` in click-repl sets defaults then calls `defaults.update(prompt_kwargs)`. User-provided keys WIN. So passing `"history": FileHistory(...)` in `prompt_kwargs` overrides the default `InMemoryHistory()`. The `ClickCompleter` is still injected as default (not overridden) so tab completion works automatically.

```python
# Internal bootstrap_prompt() behavior (verified from source):
defaults = {
    "history": InMemoryHistory(),       # ← overridden by our FileHistory
    "completer": ClickCompleter(...),   # ← kept (we don't override this)
    "message": "> ",                    # ← overridden by our "attio> "
}
defaults.update(prompt_kwargs)          # our keys win
```

### Pattern 3: Exception Handling in REPL Loop

click-repl 0.3.0 already handles:
- `KeyboardInterrupt` → continues the loop (Ctrl-C recovers without crash)
- `EOFError` → breaks the loop (Ctrl-D exits)
- `click.ClickException` → calls `e.show()` then continues
- `ClickExit`, `SystemExit` → silently passes (commands that call `sys.exit()` don't crash the REPL)
- `CommandLineParserError` → continues (bad command line parsing)
- `ExitReplException` → breaks (`:quit` meta-command)

**REPL-04 is satisfied by click-repl's built-in exception handling.** No custom exception wrapping needed in `repl.py`. The one gap: unexpected `Exception` subclasses not caught by click-repl. To be safe, the plan may add an outer `except Exception` in `repl_cmd` around `click_repl_run()` — but this is unlikely to be needed.

### Pattern 4: REPL Testing (Non-TTY Mode)

click-repl detects `sys.stdin.isatty()`. When stdin is NOT a TTY, it calls `sys.stdin.readline().strip()` in a loop. CliRunner sets stdin to a non-TTY `BytesIO`, which means REPL commands can be fed via piped input.

```python
# Source: click-repl test suite pattern (verified from GitHub)
import io
from unittest.mock import patch

def test_repl_dispatches_command(runner, mock_client):
    # Feed "people list --json\n\n" as piped stdin
    # Empty line causes non-TTY mode to break the loop
    with patch("cli_anything.attio.attio_cli.load_config", ...):
        with patch("cli_anything.attio.attio_cli.AttioClient", ...):
            result = runner.invoke(cli, ["repl"], input="people list --json\n\n")
    assert result.exit_code == 0
```

**Key insight:** In non-TTY mode, an empty line causes the REPL loop to `break`. Feed commands with `\n` terminator, then a final empty `\n` to exit cleanly. This is the correct pattern for test_repl.py.

**Alternative pattern** (direct invocation, no CliRunner):
```python
import io
import sys

def test_repl_with_mock_stdin(capsys, mock_client):
    fake_stdin = io.StringIO("people list --json\n\n")
    with patch.object(sys, "stdin", fake_stdin):
        from cli_anything.attio.repl import repl_cmd
        # ... invoke via context
```

CliRunner approach is simpler and aligns with the existing test suite pattern — use it.

### Pattern 5: --yes Flag (Already Done)

Verified: `--yes` is implemented consistently across all 7 modules that have delete operations:
- `records.py` — both `delete_cmd` in `_make_record_commands` and standalone `records_delete`
- `notes.py` — `notes_delete`
- `tasks.py` — `tasks_delete`
- `comments.py` — `comments_delete`
- `entries.py` — `entries_delete`
- `files.py` — `delete_cmd`
- `webhooks.py` — `delete_cmd`

All follow identical pattern: `@click.option("--yes", is_flag=True)` + `if not yes: click.confirm(..., abort=True)`.

**No new code required for REPL-05.** The planner should verify existing tests cover the `--yes` path.

### Pattern 6: E2E Test Structure

```python
# agent-harness/cli_anything/attio/tests/test_e2e.py
import os
import pytest
from click.testing import CliRunner
from cli_anything.attio.attio_cli import cli

ATTIO_API_KEY = os.getenv("ATTIO_API_KEY")
e2e = pytest.mark.skipif(
    not ATTIO_API_KEY,
    reason="ATTIO_API_KEY not set — skipping E2E tests"
)

@e2e
class TestE2EWorkspace:
    def test_workspace_self(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["workspace", "self", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output.strip().split("\n")[0])
        assert "id" in data

    def test_people_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["people", "list", "--json", "--limit", "1"])
        assert result.exit_code == 0
```

### Pattern 7: setup.py Entry Points — Adding `attio` Alias

```python
# setup.py — current state (only cli-anything-attio):
entry_points={
    "console_scripts": [
        "cli-anything-attio=cli_anything.attio.attio_cli:cli",
    ],
}

# After change — add attio alias:
entry_points={
    "console_scripts": [
        "cli-anything-attio=cli_anything.attio.attio_cli:cli",
        "attio=cli_anything.attio.attio_cli:cli",
    ],
}
```

After editing setup.py: `pip install -e .` to register the new entry point.

### Pattern 8: SKILL.md Format (CLI-Anything Convention)

Based on existing `.claude/skills/*/SKILL.md` format in this workspace and CLI-Anything CONTRIBUTING.md requirements:

```markdown
---
name: attio-cli
description: >
  Full Attio CRM CLI for AI agents. 20 command groups covering records, notes,
  tasks, comments, lists, entries, objects, attributes, files, meetings, webhooks,
  and workspace. Use when you need to read or write Attio CRM data from an agent.
  Supports --json flag for machine-readable output on all commands.
version: 0.1.0
maturity: validated
triggers:
  - attio records
  - attio people
  - create a note in attio
  - list attio tasks
  - search attio
  - attio webhook
  - ...
---

# Attio CLI

## Auth Setup
...

## Commands Table
| Command | Description |
| ------- | ----------- |
| `attio people list` | List all people records |
...

## Agent Usage Patterns
...
```

### Anti-Patterns to Avoid
- **Using `register_repl(cli)` directly:** This registers the REPL with no `prompt_kwargs`, giving only `InMemoryHistory()` — history is lost on exit. Always call `click_repl.repl()` directly from a custom command.
- **Assuming click-repl is installed:** It's not in setup.py `install_requires` yet — add it before implementing `repl.py`.
- **Testing REPL with CliRunner and no `input=` argument:** Without `input=`, the REPL blocks waiting for stdin. Always pass `input="command\n\n"` (trailing empty line exits non-TTY mode).
- **Running E2E tests in CI without guard:** Always use `pytest.mark.skipif(not os.getenv("ATTIO_API_KEY"), ...)` — never hard-code the key or let E2E run without the env var.
- **Creating `~/.config/attio/` inside the `FileHistory()` call:** `FileHistory` doesn't create parent directories. Call `Path(...).mkdir(parents=True, exist_ok=True)` before instantiating `FileHistory`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tab completion inside REPL | Custom completer | `ClickCompleter` (built into click-repl) | Auto-discovers all registered commands from the Click group |
| REPL exception recovery | Custom try/except loop | click-repl's built-in handler | Already handles ClickException, SystemExit, KeyboardInterrupt, EOFError |
| Persistent history | Custom readline wrapper | `prompt_toolkit.history.FileHistory` | Thread-safe, handles file creation, supports `os.PathLike` |
| HTTP mocking in tests | `responses`, `unittest.mock` patches | `pytest-httpx` HTTPXMock fixture | Already installed; integrates with httpx transport layer, no monkey-patching |

---

## Common Pitfalls

### Pitfall 1: click-repl Not in install_requires
**What goes wrong:** `ImportError: No module named 'click_repl'` when running `attio repl`
**Why it happens:** click-repl is only specified in the tech stack docs, not yet in `setup.py`
**How to avoid:** Add `"click-repl>=0.3.0"` to `install_requires` in setup.py before implementing repl.py
**Warning signs:** `ImportError` on `from click_repl import repl`

### Pitfall 2: REPL History File Parent Directory
**What goes wrong:** `FileNotFoundError` when `FileHistory` tries to open `~/.config/attio/history` if `~/.config/attio/` doesn't exist
**Why it happens:** `FileHistory` opens the file but doesn't create parent directories
**How to avoid:** Call `Path.home() / ".config/attio"` with `.mkdir(parents=True, exist_ok=True)` before constructing `FileHistory`
**Warning signs:** First-time run fails with `FileNotFoundError: [Errno 2] No such file or directory`

### Pitfall 3: REPL Test Hangs Without Input
**What goes wrong:** `runner.invoke(cli, ["repl"])` hangs indefinitely
**Why it happens:** No `input=` argument — CliRunner creates an empty stdin that blocks on readline
**How to avoid:** Always pass `input="your_command\n\n"` — the trailing empty line triggers the non-TTY `break`
**Warning signs:** Test never completes, has to be killed with Ctrl-C

### Pitfall 4: pytest-httpx Version Mismatch
**What goes wrong:** Import errors or fixture failures when running tests
**Why it happens:** pytest-httpx 0.35+ changed some internal APIs vs older versions
**How to avoid:** pytest-httpx 0.36.0 + httpx 0.28.1 are confirmed compatible — test_client.py already uses this combination successfully. Pin `pytest-httpx>=0.35` in setup.py dev extras (current spec is correct).
**Warning signs:** `HTTPXMock` not found as fixture, or `httpx_mock.add_response()` raises `TypeError`

### Pitfall 5: register_repl() vs Direct repl() Call
**What goes wrong:** No persistent history — every REPL session starts fresh
**Why it happens:** `register_repl(cli)` doesn't allow injecting `prompt_kwargs` — it registers the raw `repl()` function which defaults to `InMemoryHistory()`
**How to avoid:** Always use a custom `@cli.command()` that calls `click_repl.repl(ctx, prompt_kwargs={...})` directly
**Warning signs:** Arrow-up key shows no previous commands after restarting the REPL

### Pitfall 6: REPL Inside attio_cli.py Group Invocation
**What goes wrong:** `cli` group's `invoke_without_command` check runs `client.ensure_valid()` before the REPL command is dispatched — this means the REPL requires a valid API key even to start
**Why it happens:** The `cli` group's callback (in attio_cli.py) runs `load_config()` and `client.ensure_valid()` for every non-config subcommand, including `repl`
**How to avoid:** The current attio_cli.py already skips auth for `"config"` and `"completion"` subcommands. The REPL command should NOT be added to this skip list — authentication before entering the REPL is correct behavior. Document this clearly in ATTIO.md.
**Warning signs:** None needed — this is correct behavior.

---

## Code Examples

### Complete repl.py

```python
# Source: Derived from click-repl 0.3.0 source (github.com/click-contrib/click-repl)
# and prompt-toolkit 3.0.52 FileHistory API
"""Interactive REPL for the Attio CLI."""
from pathlib import Path

import click
from click_repl import repl as click_repl_run
from prompt_toolkit.history import FileHistory


def _ensure_history_dir() -> str:
    """Create ~/.config/attio/ if needed and return the history file path."""
    history_dir = Path.home() / ".config" / "attio"
    history_dir.mkdir(parents=True, exist_ok=True)
    return str(history_dir / "history")


def register_repl_command(cli_group: click.Group) -> None:
    """Register `repl` subcommand on cli_group with persistent FileHistory."""

    @cli_group.command("repl")
    @click.pass_context
    def repl_cmd(ctx: click.Context) -> None:
        """Start an interactive REPL session with persistent history.

        Arrow-up/down for history, Tab for completion, Ctrl-D or :quit to exit.
        Commands: any attio subcommand works here.
        """
        prompt_kwargs: dict = {
            "history": FileHistory(_ensure_history_dir()),
            "message": "attio> ",
        }
        click_repl_run(ctx, prompt_kwargs=prompt_kwargs)
```

### FileHistory API (prompt-toolkit 3.0.52)

```python
# Source: prompt-toolkit docs + WebSearch verification (March 2026)
from prompt_toolkit.history import FileHistory

# Constructor: FileHistory(filename: str | bytes | PathLike)
# The filename parameter is positional.
history = FileHistory("/home/user/.config/attio/history")

# Used as the "history" key in PromptSession kwargs:
from prompt_toolkit import PromptSession
session = PromptSession(history=history)

# In click-repl prompt_kwargs context:
prompt_kwargs = {"history": FileHistory(path_string)}
```

### HTTPXMock fixture usage (pytest-httpx 0.36)

```python
# Source: Verified from test_client.py in this codebase + official docs
from pytest_httpx import HTTPXMock

def test_something(client: AttioClient, httpx_mock: HTTPXMock):
    # Add a canned response
    httpx_mock.add_response(
        url="https://api.attio.com/v2/objects/people/records/rec_abc123",
        json={"id": {"record_id": "rec_abc123"}, "values": {}},
        status_code=200,
    )
    # Add reusable response (for retry tests)
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "1.0"}, is_reusable=True)

    # Assert requests were made
    requests = httpx_mock.get_requests()
    assert requests[0].headers["Authorization"] == "Bearer test_key"

    # Suppress "not all responses were requested" assertion
    # Use decorator: @pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
```

### E2E Skip Guard Pattern

```python
# Source: pytest docs + context from CONTEXT.md requirements
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("ATTIO_API_KEY"),
    reason="ATTIO_API_KEY not set — skipping E2E tests"
)
# OR per-class:
e2e = pytest.mark.skipif(not os.getenv("ATTIO_API_KEY"), reason="ATTIO_API_KEY required")

@e2e
class TestE2ERecords:
    ...
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `register_repl(group)` — no history control | Custom command calling `repl(ctx, prompt_kwargs=...)` | click-repl 0.3.0 (current) | Enables FileHistory injection |
| `InMemoryHistory` default | `FileHistory` via prompt_kwargs | N/A | Persistent history across sessions |
| requests + responses mock | httpx + pytest-httpx | Phase 1 decision | HTTPXMock is simpler and more precise |

---

## Open Questions

1. **click-repl version in the attio-cli venv**
   - What we know: Not in setup.py `install_requires`, not installed
   - What's unclear: Whether there's a separate venv for attio-cli or it runs against global Python 3.11
   - Recommendation: Add to setup.py `install_requires` and run `pip install -e .` as Wave 0 step

2. **test_commands.py coverage completeness**
   - What we know: File exists, pattern established for records
   - What's unclear: Whether all 20 command groups have coverage or just records
   - Recommendation: Run `pytest --tb=short` on current suite to see which tests pass/fail before Wave 1

3. **SKILL.md command table depth**
   - What we know: Must follow CLI-Anything convention with commands table
   - What's unclear: How much detail per command (options, examples) vs just name+description
   - Recommendation: Name + one-line description per command. Full usage examples in ATTIO.md SOP.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest-httpx | TEST-01, TEST-05 | Yes (global Python 3.11) | 0.36.0 | — |
| httpx | All tests | Yes (global Python 3.11) | 0.28.1 | — |
| click-repl | REPL-01, REPL-02, REPL-03, REPL-04 | No — not in setup.py | 0.3.0 needed | None — must install |
| prompt-toolkit | REPL-02 (FileHistory) | Yes (in setup.py) | 3.0.52 | — |
| Python 3.10+ | All | Yes | 3.11 (global) | — |

**Missing dependencies with no fallback:**
- click-repl — must be added to `setup.py install_requires` and installed before implementing repl.py

---

## Sources

### Primary (HIGH confidence)
- click-repl 0.3.0 `_repl.py` source — fetched from raw.githubusercontent.com — `repl()`, `register_repl()`, `bootstrap_prompt()` exact signatures
- click-repl 0.3.0 `core.py` source — fetched from GitHub — `ReplContext`, `PromptSession(**prompt_kwargs)` wiring
- click-repl test suite (GitHub) — non-TTY `sys.stdin.readline()` pattern, `mock_stdin` testing approach
- attio-cli codebase — verified `--yes` flag on all delete commands (grep confirmed)
- pytest-httpx official docs (colin-b.github.io) — `HTTPXMock.add_response()`, `get_requests()`, `is_reusable`, `@pytest.mark.httpx_mock()` decorator
- Global Python 3.11 env — `pip show pytest-httpx` = 0.36.0, `pip show httpx` = 0.28.1 — confirmed compatible

### Secondary (MEDIUM confidence)
- WebSearch + programcreek.com examples — `FileHistory` constructor takes positional `filename` string, used as `prompt_kwargs["history"]`
- prompt-toolkit docs (asking_for_input.html) — Cloudflare blocked; FileHistory API confirmed via WebSearch cross-reference
- CLI-Anything CONTRIBUTING.md — SKILL.md location, registry.json format, commands table requirement

### Tertiary (LOW confidence)
- CLI-Anything SKILL.md exact format — CONTRIBUTING.md only specifies location and purpose, not exact schema; format inferred from workspace `.claude/skills/*/SKILL.md` examples

---

## Metadata

**Confidence breakdown:**
- click-repl API: HIGH — verified from raw source code
- FileHistory API: HIGH — verified via multiple sources, consistent with test_client.py patterns
- pytest-httpx compatibility: HIGH — installed version confirmed, existing tests prove it works
- --yes flag status: HIGH — grep verified on codebase
- SKILL.md format: MEDIUM — inferred from workspace examples, CLI-Anything CONTRIBUTING.md doesn't specify full schema
- REPL testing pattern: HIGH — verified from click-repl test suite source

**Research date:** 2026-03-31
**Valid until:** 2026-06-30 (stable ecosystem — click, prompt-toolkit, pytest-httpx move slowly)
