---
name: attio-cli
description: >
  Full Attio CRM CLI for AI agents. 20+ command groups covering records, notes,
  tasks, comments, threads, lists, list entries, objects, attributes, files, meetings,
  webhooks, workspace, and interactive REPL. Use when you need to read or write Attio
  CRM data from an agent or terminal. Supports --json on all commands for
  machine-readable output. Supports --yes on all delete commands for non-interactive use.
version: 0.1.0
maturity: validated
triggers:
  - attio people
  - attio records
  - list attio contacts
  - create a note in attio
  - attio tasks list
  - search attio crm
  - attio webhook
  - attio lists
  - attio entries
  - attio objects
  - attio attributes
  - attio files
  - attio meetings
  - attio workspace
  - attio repl
  - query attio api
  - attio --json
---

# Attio CLI

Full CRM CLI for Attio. Built for AI agents and power users. Every Attio API v2
endpoint is available as a typed command with `--json` output.

## Auth Setup

Set your Attio API key in one of two ways:

**Option 1 — Environment variable (recommended for agents):**
```bash
export ATTIO_API_KEY=your_key_here
```

**Option 2 — Config file:**
```bash
attio config set api-key your_key_here
# Stored at: ~/.config/attio/config.toml
```

Get your API key: Attio workspace → Settings → API keys → Create key.

## Commands Table

| Command | Description |
| ------- | ----------- |
| `attio people list` | List all people records |
| `attio people get <id>` | Get a single person by record ID |
| `attio people create` | Create a person record |
| `attio people update <id>` | Update (PATCH) a person record |
| `attio people delete <id>` | Delete a person record (--yes to skip confirm) |
| `attio people search <query>` | Full-text search across people |
| `attio companies list` | List all company records |
| `attio companies get <id>` | Get a single company |
| `attio companies create` | Create a company record |
| `attio companies update <id>` | Update a company record |
| `attio companies delete <id>` | Delete a company record |
| `attio deals list` | List all deal records |
| `attio deals get <id>` | Get a deal by ID |
| `attio records list <object>` | List records for any custom object |
| `attio records get <object> <id>` | Get a record from any object |
| `attio records create <object>` | Create a record in any object |
| `attio records assert <object>` | Upsert a record (assert existence) |
| `attio notes list` | List notes (filter by record with --record-id) |
| `attio notes get <id>` | Get a note by ID |
| `attio notes create` | Create a note on a record |
| `attio notes delete <id>` | Delete a note |
| `attio tasks list` | List tasks (filter with --linked-object) |
| `attio tasks get <id>` | Get a task by ID |
| `attio tasks create` | Create a task |
| `attio tasks update <id>` | Update a task |
| `attio tasks delete <id>` | Delete a task |
| `attio comments list` | List comments on a thread |
| `attio comments get <id>` | Get a comment |
| `attio comments create` | Create a comment |
| `attio comments delete <id>` | Delete a comment |
| `attio comments resolve <id>` | Resolve a comment thread |
| `attio comments unresolve <id>` | Unresolve a comment thread |
| `attio threads list` | List comment threads |
| `attio threads get <id>` | Get a thread |
| `attio lists list` | List all Attio lists |
| `attio lists get <id>` | Get a list |
| `attio lists create` | Create a list |
| `attio lists update <id>` | Update a list |
| `attio lists delete <id>` | Delete a list |
| `attio entries list <list-id>` | List entries in a list |
| `attio entries get <list-id> <id>` | Get a list entry |
| `attio entries create <list-id>` | Add a record to a list |
| `attio entries assert <list-id>` | Upsert a list entry |
| `attio entries update <list-id> <id>` | Patch a list entry |
| `attio entries put <list-id> <id>` | Replace a list entry |
| `attio entries delete <list-id> <id>` | Remove a list entry |
| `attio objects list` | List all workspace objects |
| `attio objects get <slug>` | Get an object schema |
| `attio objects create` | Create a custom object |
| `attio objects update <slug>` | Update an object |
| `attio attributes list <object>` | List attributes for an object |
| `attio attributes get <object> <id>` | Get an attribute |
| `attio attributes create <object>` | Create an attribute |
| `attio attributes update <object> <id>` | Update an attribute |
| `attio attributes archive <object> <id>` | Archive an attribute |
| `attio files upload <path>` | Upload a file |
| `attio files get <id>` | Get file metadata |
| `attio files download <id>` | Download a file |
| `attio files delete <id>` | Delete a file |
| `attio meetings list` | List meetings |
| `attio meetings get <id>` | Get a meeting |
| `attio webhooks list` | List webhook subscriptions |
| `attio webhooks get <id>` | Get a webhook |
| `attio webhooks create` | Create a webhook subscription |
| `attio webhooks delete <id>` | Delete a webhook |
| `attio workspace self` | Get current workspace info |
| `attio workspace members` | List workspace members |
| `attio config set <key> <value>` | Set config value (api-key, base-url) |
| `attio config get <key>` | Get a config value |
| `attio config list` | List all config values |
| `attio repl` | Start interactive REPL with history + tab completion |
| `attio completion --shell bash` | Print shell completion setup |

## Agent Usage Patterns

**Always use `--json` for machine-readable output:**
```bash
attio people list --json
attio notes list --json --record-id rec_abc123
```

**Skip confirmation on destructive operations:**
```bash
attio notes delete note_abc123 --yes
attio tasks delete task_abc123 --yes
```

**Paginate large result sets:**
```bash
# Get first 50 results
attio people list --json --limit 50

# Get all results (streams all pages)
attio people list --json --all
```

**Exit codes:**
- `0` — success
- `1` — command error (bad arguments, API 4xx)
- `2` — usage error (missing required argument)
- `4` — auth error (missing or invalid API key)
- `5` — rate limit error (429, after retries exhausted)

**Filter and sort (where supported):**
```bash
attio tasks list --json --linked-object people --linked-record-id rec_abc123
attio notes list --json --record-id rec_abc123
```
