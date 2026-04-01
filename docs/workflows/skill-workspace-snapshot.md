---
name: workspace-snapshot
description: >
  Instant Attio workspace health check. Pulls record counts per object, active lists
  with entry counts, open task count, and workspace member count. Use before a client
  call, for weekly reporting, or any time you need a fast status read on the CRM.
triggers:
  - workspace snapshot
  - attio health check
  - how many records in attio
  - attio summary
  - weekly attio report
  - crm snapshot
  - attio status
---

# workspace-snapshot

Quick health check of an Attio CRM workspace. Read-only. No writes. Runs in under 10 seconds.

## Purpose

Before a client call or during weekly review, get a one-glance picture of the workspace:
which objects exist, how many records are in each, what lists are active and how full
they are, how many open tasks are sitting unresolved, and who has workspace access.
No auth beyond the normal API key. No arguments required.

## Trigger

- Ad-hoc: "give me a workspace snapshot" / "how's the attio workspace looking"
- Scheduled: weekly review (pair with `/leadgrow:weekly-review` or Friday client report)

## Inputs

None required.

| Option | Default | Description |
|---|---|---|
| `--output table` | default | Rich-formatted terminal table |
| `--output json` | — | Raw JSON from each command, one block per section |

The `--json` flag on individual commands is what drives JSON output mode — see Steps below.

## Steps

Run these commands in sequence. Each is independent; failure of one doesn't block the rest.

### 1. Workspace identity

```bash
attio workspace self
```

Returns workspace name, slug, and authenticated token info. Confirms you're pointed at the right workspace.

### 2. Object types and record counts

```bash
# List all object types (standard + custom)
attio objects list --json

# For each object slug returned, pull a page-1 count
attio records list <object_slug> --limit 1 --json
attio people list --limit 1 --json
attio companies list --limit 1 --json
attio deals list --limit 1 --json
```

The `--limit 1` call returns `total` in the response metadata — use that number as the
record count. No need to paginate all records.

Standard slugs always present: `people`, `companies`, `deals`, `users`, `workspaces`.
Custom objects appear in `attio objects list` output under `.data[].api_slug`.

### 3. Active lists with entry counts

```bash
# Get all lists
attio lists list --json

# For each list ID, pull entry count
attio entries list <list_id> --limit 1 --json
```

Extract `list.id` and `list.name` from the lists response. Use entry response `total`
for entry count. Flag lists with 0 entries as inactive (still show them, just note it).

### 4. Open tasks

```bash
attio tasks list --not-completed --json
```

Count the records returned. This is the open task count. Optionally surface the 3 most
overdue (sort by `deadline_at` ascending, nulls last).

### 5. Workspace members

```bash
attio workspace members --json
```

Count of active members. Useful sanity check that no seats have been added/removed unexpectedly.

## Output Format

Render as three stacked tables with a header line.

```
Attio Workspace Snapshot — [workspace name]  |  [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OBJECTS & RECORDS
┌──────────────────┬────────┐
│ Object           │ Count  │
├──────────────────┼────────┤
│ People           │  1,847 │
│ Companies        │    412 │
│ Deals            │     93 │
│ Users            │     14 │
│ custom_obj_slug  │     61 │
└──────────────────┴────────┘

ACTIVE LISTS
┌──────────────────────────────┬─────────────────────┬─────────┐
│ List Name                    │ ID (short)          │ Entries │
├──────────────────────────────┼─────────────────────┼─────────┤
│ Q2 Outbound Pipeline         │ …3a1f               │     142 │
│ Demo Booked                  │ …c88b               │      27 │
│ Closed Won 2025              │ …f02d               │      58 │
│ Stale — No Activity          │ …9e4c               │       0 │
└──────────────────────────────┴─────────────────────┴─────────┘

TASKS & WORKSPACE
┌──────────────────────┬───────┐
│ Metric               │ Value │
├──────────────────────┼───────┤
│ Open tasks           │    11 │
│ Workspace members    │     4 │
└──────────────────────┴───────┘
```

If `--output json` is passed, skip rich tables and print a single JSON object:

```json
{
  "workspace": "LeadGrow",
  "snapshot_at": "2026-03-31T09:00:00Z",
  "objects": [
    { "name": "People", "slug": "people", "count": 1847 },
    { "name": "Companies", "slug": "companies", "count": 412 }
  ],
  "lists": [
    { "name": "Q2 Outbound Pipeline", "id": "abc123", "entries": 142 }
  ],
  "open_tasks": 11,
  "workspace_members": 4
}
```

## Example Output

```
Attio Workspace Snapshot — LeadGrow  |  2026-03-31

OBJECTS & RECORDS
┌───────────────┬────────┐
│ Object        │ Count  │
├───────────────┼────────┤
│ People        │  1,847 │
│ Companies     │    412 │
│ Deals         │     93 │
│ Users         │     14 │
└───────────────┴────────┘

ACTIVE LISTS
┌──────────────────────────┬─────────┐
│ List Name                │ Entries │
├──────────────────────────┼─────────┤
│ Q2 Outbound Pipeline     │     142 │
│ Demo Booked              │      27 │
│ Closed Won 2025          │      58 │
└──────────────────────────┴─────────┘

TASKS & WORKSPACE
┌───────────────────┬───────┐
│ Metric            │ Value │
├───────────────────┼───────┤
│ Open tasks        │    11 │
│ Workspace members │     4 │
└───────────────────┴───────┘
```

## CLI Commands Used

| Command | Purpose |
|---|---|
| `attio workspace self` | Workspace identity and auth confirmation |
| `attio objects list --json` | All object types including custom objects |
| `attio people list --limit 1 --json` | People record count (via `total` field) |
| `attio companies list --limit 1 --json` | Company record count |
| `attio deals list --limit 1 --json` | Deal record count |
| `attio records list <slug> --limit 1 --json` | Count for any custom object |
| `attio lists list --json` | All lists with IDs and names |
| `attio entries list <list_id> --limit 1 --json` | Entry count per list |
| `attio tasks list --not-completed --json` | All open tasks |
| `attio workspace members --json` | Workspace member count |

## Implementation Notes

- **Record count trick:** Every paginated response from the attio CLI includes a `total`
  field in the metadata. Fetch `--limit 1` to get the count without pulling all records.
  If the CLI doesn't expose `total` in its current table output, use `--json` and parse
  `response.total` or `response.meta.total` depending on which the Attio v2 API returns
  for that endpoint.

- **Custom objects:** `attio objects list` returns all objects. Filter out the 5 standard
  slugs (`people`, `companies`, `deals`, `users`, `workspaces`) and loop over the rest
  with `attio records list <slug> --limit 1 --json`.

- **List entry counts:** The entries endpoint doesn't guarantee a top-level `total` on
  all versions — if missing, fall back to counting returned records at `--limit 500`
  and paginating with `--all`. For snapshot purposes, approximate is fine.

- **Error handling:** If any single command 404s (e.g., a list was deleted), log
  "N/A" for that row and continue. The snapshot should never hard-fail on a partial
  workspace state.

- **Output flag propagation:** Pass `--json` to every attio command when `--output json`
  is selected. Strip rich formatting entirely. Write raw aggregated JSON to stdout.
