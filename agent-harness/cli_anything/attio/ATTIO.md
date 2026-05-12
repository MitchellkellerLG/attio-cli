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
Note: `.env` is loaded from the current working directory. For persistent auth across
directories, use `attio config set` instead.

**Check current config:**
```bash
attio config list
```

Get your API key: Attio workspace → Settings → API → API keys → Generate key.

## Command Reference

All commands support `--help` and `--json`. Delete commands support `--yes` to skip confirmation.

### Records

```bash
# Standard objects: people, companies, deals, users, workspaces
attio people list --json --limit 10
attio people list --json --all                  # Stream all pages
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
attio records update <object-slug> <record-id> --data '{...}'
attio records delete <object-slug> <record-id> --yes
attio records assert <object-slug> --matching-attribute email --data '{...}'
attio records search <object-slug> "query" --json
```

### Notes

```bash
attio notes list --json
attio notes list --json --parent-record-id rec_abc123 --parent-object people  # Filter by record
attio notes get <note-id> --json
attio notes create --parent-object people --parent-record-id rec_abc123 --title "Call notes" --content "..."
attio notes update <note-id> --title "Updated title"
attio notes update <note-id> --content "Updated content"
attio notes delete <note-id> --yes
```

### Tasks

```bash
attio tasks list --json
attio tasks list --json --linked-object people --linked-record-id rec_abc123
attio tasks get <task-id> --json
attio tasks create --content "Follow up with Jane" --deadline "2026-04-01T12:00:00Z" --assignee-id usr_abc123
attio tasks update <task-id> --is-completed true
attio tasks update <task-id> --content "Updated content"
attio tasks delete <task-id> --yes
```

### Comments and Threads

```bash
# Comments
attio comments create --record-id rec_abc123 --body "Great meeting!"
attio comments create --thread-id thrd_abc123 --body "Reply text"  # Reply to existing thread
attio comments get <comment-id> --json
attio comments resolve <comment-id>    # Mark thread resolved
attio comments unresolve <comment-id>
attio comments delete <comment-id> --yes

# Threads (view comment threads on records or entries)
attio threads list --record-id rec_abc123 --json
attio threads get <thread-id> --json    # Includes all comments
```

### Lists and Entries

```bash
# Lists
attio lists list --json
attio lists get <list-id> --json
attio lists create --name "Hot Leads" --parent-object people
attio lists update <list-id> --name "New Name"
attio lists views <list-id> --json      # List saved views

# List entries
attio entries list <list-id> --json
attio entries list <list-id> --json --all   # All pages
attio entries get <list-id> <entry-id> --json
attio entries create <list-id> --parent-record-id rec_abc123
attio entries assert <list-id> --parent-record-id rec_abc123   # Idempotent add
attio entries update <list-id> <entry-id> --data '{...}'
attio entries put <list-id> <entry-id> --data '{...}'   # Full replace
attio entries delete <list-id> <entry-id> --yes
```

### Objects and Attributes

```bash
# Objects (read + create + update, no delete — Attio disallows it)
attio objects list --json
attio objects get people --json
attio objects create --slug custom_thing --singular "Thing" --plural "Things"
attio objects update <object-id> --data '{"singular_noun": "Widget"}'
attio objects views <object-id> --json   # List saved views for an object

# Attributes
attio attributes list --object people --json
attio attributes list --list <list-id> --json
attio attributes get people <attribute-slug> --json
attio attributes create --object people --title "Lead Score" --slug lead_score --type number
attio attributes update people <attribute-slug> --data '{"title": "New Title"}'
attio attributes archive people <attribute-slug>   # Soft delete (permanent)

# Select options (for select-type attributes)
attio attributes options people <attribute-slug> --json
attio attributes options-create people <attribute-slug> --title "High Priority"

# Status values (for status-type attributes)
attio attributes statuses people <attribute-slug> --json
attio attributes statuses-create people <attribute-slug> --title "Active"
```

### Files

```bash
attio files upload ./contract.pdf --record-id rec_abc123 --object people --json
attio files list --json
attio files list --record-id rec_abc123 --json   # Filter by record
attio files get <file-id> --json
attio files download <file-id> --output ./contract-copy.pdf
attio files create-folder --name "Documents" --record-id rec_abc123 --object people
attio files delete <file-id> --yes
```

### Meetings

```bash
attio meetings list --json
attio meetings get <meeting-id> --json
attio meetings recordings <meeting-id> --json   # List recordings for a meeting
attio meetings transcript <meeting-id> <recording-id> --json   # Get transcript
```

### Webhooks

```bash
attio webhooks list --json
attio webhooks get <webhook-id> --json
attio webhooks create --target-url https://example.com/hook --subscriptions '[{"event_type": "record.created"}]'
attio webhooks update <webhook-id> --data '{"status": "inactive"}'
attio webhooks delete <webhook-id> --yes
```

### Workspace

```bash
attio workspace self --json        # Current workspace identity and API key info
attio workspace members --json     # List all workspace members
attio workspace member <member-id> --json  # Get a specific member
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

## Agent Workflow Patterns

### Pattern 1: GTM workflow (search → note → task → list entry)

```bash
# Find the record
RECORD_ID=$(attio people search "Jane Doe" --json | jq -r '.data[0].id.record_id')

# Add a note
attio notes create --parent-object people --parent-record-id "$RECORD_ID" --title "Discovery call" --content "Discussed Q4 budget."

# Add a follow-up task
attio tasks create --content "Send proposal to Jane" --deadline "2026-04-01T12:00:00Z"

# Add to pipeline list
LIST_ID="list_xyz123"
attio entries assert "$LIST_ID" --parent-record-id "$RECORD_ID"
```

### Pattern 2: Paginate large datasets

```bash
# Stream all records (handles offset pagination automatically)
attio people list --json --all > all_people.jsonl
attio entries list <list-id> --json --all > all_entries.jsonl
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
attio entries delete <list-id> entry_abc123 --yes
```

### Pattern 5: Check workspace before running

```bash
attio workspace self --json
# Exits 4 if API key is missing or invalid — catch this before other commands
```

### Pattern 6: Schema introspection

```bash
# Discover what attributes exist on an object
attio attributes list --object people --json | jq '.data[].api_slug'

# Get select options for a field
attio attributes options people lead_source --json | jq '.data[].title'
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

Stored at `~/.config/attio/config.json`:

```json
{
  "api_key": "your_key_here",
  "base_url": "https://api.attio.com/v2"
}
```

Managed via `attio config` commands. Environment variable `ATTIO_API_KEY` takes
precedence over the config file.
