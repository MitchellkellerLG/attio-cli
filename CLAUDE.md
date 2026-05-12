## Project

Attio CLI — full Attio CRM REST API v2 coverage as a CLI tool. Built with the CLI-Anything framework. Entry point: `attio` (or `cli-anything-attio`). Python 3.10+.

## Install & Run

```bash
# From repo root — editable install
pip install -e .

# Verify
attio --help

# Run tests
pytest
pytest agent-harness/cli_anything/attio/tests/ -v
```

## Architecture

```
agent-harness/cli_anything/attio/   # All CLI source code
  attio_cli.py                      # Click app entry point, command group wiring
  records.py / people / companies   # Per-resource command modules
  notes.py, tasks.py, lists.py      # etc.
  entries.py                        # List membership commands
  objects.py, attributes.py         # Schema management
  files.py, meetings.py             # File upload, meetings (read-only)
  webhooks.py, workspace.py         # Webhooks, workspace identity
  repl.py                           # Interactive REPL (prompt-toolkit + click-repl)
  utils/                            # HTTP client, config loader, shared helpers
  tests/                            # pytest unit + E2E tests
  ATTIO.md                          # Full command reference SOP — read this for usage
  SKILL.md                          # CLI-Anything skill definition
skills/                             # GTM skills (pipeline-snapshot, overdue-follow-up, etc.)
docs/workflows/                     # n8n workflow specs
.planning/                          # GSD planning artifacts (phases, STATE.md, HANDOFF.json)
```

## Auth — Three Methods (Priority Order)

1. **Config file (persistent, recommended):** `attio config set api-key YOUR_KEY` — stored at `~/.config/attio/config.toml`
2. **Env var (CI/agents):** `ATTIO_API_KEY=your_key attio ...` or `export ATTIO_API_KEY=...`
3. **.env file:** `ATTIO_API_KEY=your_key` in repo root — only loaded if `attio` runs from that directory

Env var takes precedence over config file. Check current: `attio config list`.

## Key Gotchas

- **`--json` flag is required for agent consumption.** Without it, output is rich-formatted for humans. Always pass `--json` in scripts and pipelines.
- **`--yes` flag skips confirmation on deletes.** Required for non-interactive agent pipelines — `attio notes delete <id> --yes`.
- **`entries assert` is idempotent; `entries create` is not.** Use `assert` when you're not sure if a record is already in a list.
- **`attributes archive` — not delete.** Attio doesn't allow hard-deleting attributes. Use `attio attributes archive <object> <attr-id>`.
- **Exit code 4 = auth failure** (missing/invalid key). Exit code 5 = rate limit exhausted after retries. Always check exit code 4 before blaming other errors.
- **Config file is JSON:** stored at `~/.config/attio/config.json`. Some older docs may say `.toml` — that's wrong. The `attio config set` command writes JSON.
- **Two entry points:** `attio` and `cli-anything-attio` — both work, same binary. `attio` is the short form.
- **Packages root is `agent-harness/`**, not the repo root. `setuptools` is configured with `where = ["agent-harness"]` in pyproject.toml. Import as `cli_anything.attio.*`.
- **Search payload bug was patched:** `request_as: None` caused 400s on every `attio * search` call — fixed in latest commit. If seeing 400s on search, check you're on latest.
- **REPL history** persists at `~/.config/attio/history`. Arrow-up cycles previous commands.

## Full Command Reference

See `agent-harness/cli_anything/attio/ATTIO.md` — covers every command group with examples, agent workflow patterns, exit codes, and pagination (`--all` flag for streaming full datasets).

## Stack

Click 8.3+, httpx 0.28+, tenacity 9.1+ (retry/backoff), rich 14.3+ (human output), prompt-toolkit 3.0+ (REPL), python-dotenv (`.env` loading), rich-click (help formatting), click-repl (REPL wiring). Dev: pytest, pytest-httpx (mock HTTP), ruff, mypy strict.
