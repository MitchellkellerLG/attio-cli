# attio-cli

Full Attio CRM v2 API coverage as a typed, documented CLI. Every object, note, task, and webhook accessible from the terminal — designed for AI agents and power users who need Attio fully controllable via shell.

```bash
attio people search "Sarah Chen" --json
attio tasks list --not-completed --json
attio notes create --parent-object people --parent-record-id rec_01abc --title "Discovery call" --content "..."
```

---

## Install

**Recommended: uv (fast)**

```bash
git clone https://github.com/MitchellkellerLG/attio-cli.git
cd attio-cli
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e .
```

**Alternative: pip**

```bash
git clone https://github.com/MitchellkellerLG/attio-cli.git
cd attio-cli
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Verify:

```bash
attio --version
attio --help
```

---

## Auth

Get your API key from **Attio → Settings → API → Generate key**.

**Option 1 — Environment variable (recommended)**

```bash
export ATTIO_API_KEY=your_key_here
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

**Option 2 — .env file**

Copy the example and fill it in:

```bash
cp .env.example .env
# Edit .env and set ATTIO_API_KEY
```

**Option 3 — Config file**

```bash
attio config set api-key your_key_here
# Stored at ~/.config/attio/config.json
```

Verify auth works:

```bash
attio workspace self
```

---

## Quick Start

```bash
# Find a contact
attio people search "Jordan Lee"

# Get their full record as JSON
attio people get rec_01abc123 --json

# Create a note after a call
attio notes create \
  --parent-object people \
  --parent-record-id rec_01abc123 \
  --title "Discovery call — March 31" \
  --content "Discussed Q2 pipeline. Budget confirmed at $5k/mo. Follow up mid-April."

# Create a follow-up task
attio tasks create \
  --content "Send proposal to Jordan" \
  --deadline "2026-04-07T17:00:00Z" \
  --linked-object people \
  --linked-record-id rec_01abc123

# List overdue tasks
attio tasks list --not-completed --json | jq '[.[] | select(.deadline_at < now | todate)]'

# List all active deals
attio deals list --json
```

---

## Command Reference

All commands support `--json` for raw JSON output (agent-friendly) and `--help` for usage details.

### People

| Command | Description |
|---------|-------------|
| `attio people search <query>` | Fuzzy search by name |
| `attio people search --email <email>` | Search by email address |
| `attio people get <id>` | Fetch full record by ID |
| `attio people list` | List all people records |
| `attio people list --filter key=value` | Filter by attribute |
| `attio people create --values <json>` | Create a new person |
| `attio people update <id> --values <json>` | Update (PATCH — append multiselect) |
| `attio people update <id> --values <json> --overwrite` | Overwrite (PUT — replace multiselect) |
| `attio people assert --matching-attribute email --values <json>` | Create or update by matching attribute |
| `attio people delete <id>` | Delete a person record |

### Companies

Same subcommands as `people`: `search`, `get`, `list`, `create`, `update`, `assert`, `delete`.

### Deals

Same subcommands as `people`: `search`, `get`, `list`, `create`, `update`, `assert`, `delete`.

### Notes

| Command | Description |
|---------|-------------|
| `attio notes create` | Create a note on any record |
| `attio notes get <id>` | Get note by ID |
| `attio notes list` | List all notes |
| `attio notes list --parent-object <obj> --parent-record-id <id>` | Notes on a specific record |
| `attio notes update <id>` | Update note title or content |
| `attio notes delete <id>` | Delete a note |

### Tasks

| Command | Description |
|---------|-------------|
| `attio tasks create` | Create a task with assignees and linked records |
| `attio tasks get <id>` | Get task by ID |
| `attio tasks list` | List all tasks |
| `attio tasks list --not-completed` | Only incomplete tasks |
| `attio tasks list --linked-object <obj> --linked-record-id <id>` | Tasks on a specific record |
| `attio tasks update <id> --deadline <iso8601>` | Push task deadline |
| `attio tasks update <id> --completed` | Mark task complete |
| `attio tasks delete <id>` | Delete a task |

### Webhooks

| Command | Description |
|---------|-------------|
| `attio webhooks create --target-url <url> --events <event,...>` | Subscribe to events |
| `attio webhooks get <id>` | Get webhook by ID |
| `attio webhooks list` | List all webhook subscriptions |
| `attio webhooks update <id>` | Update URL or event subscriptions |
| `attio webhooks delete <id>` | Delete a subscription |

### Workspace

| Command | Description |
|---------|-------------|
| `attio workspace self` | Show current token and workspace info |
| `attio workspace members` | List all workspace members |
| `attio workspace member <id>` | Get a member by ID |

### Config

| Command | Description |
|---------|-------------|
| `attio config set api-key <key>` | Save API key to config file |
| `attio config show` | Show current config |

---

## Flags

| Flag | Applies To | Description |
|------|-----------|-------------|
| `--json` | All commands | Output raw JSON to stdout instead of Rich tables |
| `--limit <n>` | List commands | Cap results to N records |
| `--all` | List commands | Paginate through all records (streams page-by-page) |
| `--filter key=value` | List commands | Simple attribute filter shorthand |
| `--filter-file <path>` | List commands | Complex filter from a JSON file |
| `--overwrite` | Update commands | PUT (replace) instead of PATCH (append) on multiselect attributes |
| `--help` | All commands | Usage and flag descriptions |

---

## Output Behavior

- **Terminal:** Rich tables with color by default
- **Pipe / `--json`:** Raw JSON to stdout, errors to stderr
- **Exit codes:** `0` success · `1` error · `2` usage error · `3` not found · `4` auth failure · `5` rate limited

---

## AI Skills

Four interactive GTM skills for Claude Code agents. Drop the `skills/` folder into `.claude/skills/` or reference any `SKILL.md` directly in a session.

| Skill | Trigger | What It Does |
|-------|---------|--------------|
| `post-call-followup` | "write a follow-up for Sarah" | Pulls call note from Attio, generates personalized email in LeadGrow voice, review loop, creates Attio task |
| `overdue-follow-up` | "what follow-ups am I behind on" | Pulls all overdue tasks, generates per-contact message, interactive approve/edit/skip loop |
| `lead-nurture` | "who needs a touch this week" | Pulls stale contacts from an Attio list, generates tailored message per contact, queues approved to EmailBison |
| `deal-next-step` | "what should I do with the Acme deal" | Diagnoses deal state, recommends exact next action, drafts the message, creates task on approval |

All skills are interactive — Claude generates, you review, nothing sends without your explicit approval.

**Install:**

```bash
cp -r skills/ ~/.claude/skills/
```

Or in any Claude Code session, reference the skill path directly:

```
Read the skill at /path/to/attio-cli/skills/overdue-follow-up/SKILL.md and run it.
```

---

## Development Setup

```bash
# Clone and create venv
git clone https://github.com/MitchellkellerLG/attio-cli.git
cd attio-cli
uv venv && source .venv/bin/activate

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Lint + format
ruff check .
ruff format .

# Type check
mypy agent-harness/cli_anything
```

### Project Structure

```
attio-cli/
├── agent-harness/
│   └── cli_anything/
│       └── attio/          # CLI source code
│           ├── attio_cli.py     # Entry point, command groups
│           ├── client.py        # AttioClient (auth, retry, pagination)
│           ├── commands/        # One module per command group
│           └── tests/
├── skills/                 # AI agent skills for Claude Code
│   ├── post-call-followup/
│   ├── overdue-follow-up/
│   ├── lead-nurture/
│   └── deal-next-step/
├── docs/
│   └── workflows/          # n8n integration specs
├── pyproject.toml          # Build config, tool config
├── setup.py                # Package metadata and entry points
└── .env.example            # Auth setup template
```

### Running Against the Live API

Set `ATTIO_API_KEY` and run any command. The client respects Attio's rate limit (60 req/min) with automatic exponential backoff on 429s.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| click | ≥8.3.1 | CLI framework — commands, options, arguments |
| httpx | ≥0.28.1 | HTTP client — connection pooling, clean transport layer |
| tenacity | ≥9.1.4 | Retry / backoff — 429 + 5xx handling |
| rich | ≥14.3.3 | Terminal output — tables, colored JSON, progress |
| python-dotenv | ≥1.2.2 | `.env` file loading |
| prompt-toolkit | ≥3.0.52 | Interactive REPL (coming in v2) |
| rich-click | ≥1.9 | Rich-formatted `--help` output |
| click-repl | ≥0.3.0 | REPL loop wiring |

**Dev only:** `pytest`, `pytest-httpx`, `pytest-cov`, `ruff`, `mypy`

---

## n8n Workflows

Four automation workflows connecting Attio to the LeadGrow stack (EmailBison → Attio, Clay → Attio, Attio → Google Sheets, Attio → Clay). These run independently of this CLI — they hit the Attio API directly via HTTP nodes.

See [`docs/workflows/CHARLES-HANDOFF.md`](docs/workflows/CHARLES-HANDOFF.md) for the full developer handoff.

---

## Attio API Reference

- [Official API docs](https://developers.attio.com)
- Base URL: `https://api.attio.com/v2`
- Auth: `Authorization: Bearer {ATTIO_API_KEY}`
- Rate limit: 60 req/min
