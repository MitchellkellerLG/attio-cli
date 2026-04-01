# Attio CLI — SOP

Full Attio CRM CLI built with the CLI-Anything framework. Gives AI agents and power
users complete command-line access to Attio v2 API — records, notes, tasks, lists,
webhooks, and everything else the API exposes.

## Installation

```bash
# From repo root
pip install -e .

# Verify both entry points
attio --help
cli-anything-attio --help
```

Python 3.10+ required.

## Auth Setup

**Quickstart — set once, works everywhere (recommended for humans):**
```bash
attio config set api-key your_key_here
# Stored at: ~/.config/attio/config.json — no env var needed after this
```

**Environment variable (CI / agent use):**
```bash
export ATTIO_API_KEY=your_key_here   # Linux/Mac
$env:ATTIO_API_KEY = "your_key_here"  # PowerShell
```

**.env file (repo-local):**
```bash
# Create attio-cli/.env:
ATTIO_API_KEY=your_key_here
```
Note: `.env` is loaded from the current working directory. Run `attio` commands from the repo root or the directory containing `.env` for this to work. For persistent auth across directories, use `attio config set` instead.

**Check current config:**
```bash
attio config list
```

Get your API key: Attio workspace → Settings → API → API keys → Generate key.

## Command Reference

All commands support `--help` and `--json`. Delete commands support `--yes` to skip confirmation.

### Records

```bash
# Standard objects
attio people list --json --limit 10
attio people get <record-id> --json
attio people create --data '{"name": [{"first_name": "Jane", "last_name": "Doe"}]}'
attio people update <record-id> --data '{"job_title": [{"value": "CEO"}]}'
attio people delete <record-id> --yes
attio people search "Jane" --json

# Same pattern for companies, deals, users, workspaces
attio companies list --json

# Generic record group (for custom objects)
attio records list <object-slug> --json
attio records get <object-slug> <record-id> --json
attio records create <object-slug> --data '{...}'
attio records assert <object-slug> --matching-attribute email --data '{...}'
```

### Notes

```bash
attio notes list --json
attio notes list --json --record-id rec_abc123   # Filter by record
attio notes get <note-id> --json
attio notes create --record-id rec_abc123 --title "Call notes" --content "..."
attio notes delete <note-id> --yes
```

### Tasks

```bash
attio tasks list --json
attio tasks list --json --linked-object people --linked-record-id rec_abc123
attio tasks get <task-id> --json
attio tasks create --deadline "2026-04-01T12:00:00Z" --assignee-id usr_abc123
attio tasks update <task-id> --is-completed true
attio tasks delete <task-id> --yes
```

### Lists and Entries

```bash
# Lists
attio lists list --json
attio lists get <list-id> --json
attio lists create --name "Hot Leads" --object people
attio lists delete <list-id> --yes

# List entries
attio entries list <list-id> --json
attio entries create <list-id> --record-id rec_abc123
attio entries assert <list-id> --record-id rec_abc123   # Idempotent add
attio entries update <list-id> <entry-id> --data '{...}'
attio entries put <list-id> <entry-id> --data '{...}'   # Full replace
attio entries delete <list-id> <entry-id> --yes
```

### Objects and Attributes

```bash
# Objects (read + create + update, no delete)
attio objects list --json
attio objects get people --json
attio objects create --singular-noun "Deal" --plural-noun "Deals"
attio objects update people --description "..."

# Attributes (archive instead of delete)
attio attributes list people --json
attio attributes get people <attribute-id> --json
attio attributes create people --name "Lead Score" --type number
attio attributes archive people <attribute-id>   # Soft delete
```

### Files

```bash
attio files upload ./contract.pdf --json
attio files get <file-id> --json
attio files download <file-id> --output ./contract-copy.pdf
attio files delete <file-id> --yes
```

### Meetings

```bash
attio meetings list --json
attio meetings get <meeting-id> --json
```

### Webhooks

```bash
attio webhooks list --json
attio webhooks get <webhook-id> --json
attio webhooks create --target-url https://example.com/hook --subscriptions record.created
attio webhooks delete <webhook-id> --yes
```

### Workspace

```bash
attio workspace self --json     # Current workspace identity
attio workspace members --json  # All workspace members
```

## Interactive REPL

```bash
attio repl
```

Starts an interactive session. Features:
- Arrow-up/down: command history (persistent across sessions at `~/.config/attio/history`)
- Tab: command and subcommand completion
- Ctrl-D or `:quit`: exit
- Ctrl-C: cancel current input and return to prompt
- Any bad command prints an error and returns to the prompt — no crash

Example session:
```
attio> people list --json --limit 3
[{"id": ...}, ...]
attio> workspace self --json
{"id": ...}
attio> :quit
```

Note: The REPL requires a valid API key (same as all other commands).

## Agent Workflow Patterns

### Pattern 1: Read-then-write

```bash
# Find the record
RECORD_ID=$(attio people search "Jane Doe" --json | jq -r '.[0].id.record_id')

# Write to it
attio notes create --record-id "$RECORD_ID" --title "Follow-up" --content "..."
```

### Pattern 2: Paginate large datasets

```bash
# Stream all records (uses --all flag, handles cursor pagination)
attio people list --json --all > all_people.jsonl
```

### Pattern 3: Idempotent list membership

```bash
# Safe to run multiple times — won't duplicate
attio entries assert <list-id> --record-id rec_abc123
```

### Pattern 4: Non-interactive agent deletion

```bash
# --yes skips the "Are you sure?" prompt — safe for agent pipelines
attio notes delete note_abc123 --yes
attio tasks delete task_abc123 --yes
```

### Pattern 5: Check workspace before running

```bash
attio workspace self --json
# Exits 4 if API key is missing or invalid — catch this before other commands
```

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Success |
| 1 | Command error (bad arguments, API 4xx other than auth) |
| 2 | Usage error (missing required argument, bad option) |
| 4 | Auth error (missing or invalid ATTIO_API_KEY) |
| 5 | Rate limit error (429 after all retries exhausted) |

## Configuration File

Stored at `~/.config/attio/config.toml`:

```toml
api_key = "your_key_here"
base_url = "https://api.attio.com/v2"  # Override for testing
```

Managed via `attio config` commands. Environment variable `ATTIO_API_KEY` takes
precedence over the config file.
