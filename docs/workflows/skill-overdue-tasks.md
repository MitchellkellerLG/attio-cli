---
name: overdue-tasks
description: Surface all overdue tasks from Attio for morning pipeline review. Filter by assignee or object type, then mark complete, snooze, or add a note per task. Use this at the start of each day or week to clear task debt before new work enters.
triggers:
  - morning review
  - overdue tasks
  - pipeline review
  - task debt
  - daily standup
  - weekly review
---

# Skill: `overdue-tasks`

**Project:** attio-cli
**Layer:** Workflow skill (multi-command orchestration)
**Audience:** Developer implementing this as a Claude Code skill or automation wrapper

---

## Purpose

Surface all tasks in Attio where the deadline has passed and `is_completed` is false. Format them grouped by linked object for fast review. Let the user take action on each: mark complete, push the deadline, or add a note explaining status.

This is the daily pipeline hygiene workflow. Overdue tasks = dropped balls. The skill forces a decision on every one before the session ends.

---

## Trigger

**Manual** — run at the start of the workday or at the top of a weekly pipeline review.

**Scheduled option** — can be wired to a morning automation (e.g., `attio tasks list --not-completed --json` piped to a formatter script). Not interactive when scheduled; output goes to a daily digest file or Telegram message.

---

## Inputs

All inputs are optional. No flags = full overdue task list across all objects and assignees.

| Flag | Type | Description |
|------|------|-------------|
| `--assignee <actor_id>` | string | Filter to tasks assigned to a specific workspace member. Get actor IDs via `attio workspace members`. |
| `--object <slug>` | string | Limit to tasks linked to a specific object type: `people`, `deals`, `companies`. Maps to `--linked-object` on the list command. |
| `--limit <n>` | int | Cap results to N tasks. Default: show all. Useful if the backlog is large and you only want to triage the worst offenders first. |

---

## Steps

### Step 1 — Pull all incomplete tasks

```bash
attio tasks list --not-completed --json
```

This returns the full list of incomplete tasks across the workspace. No deadline filtering happens at the API level — Attio's task list endpoint does not accept a deadline range filter. Deadline filtering is done client-side in Step 2.

**With assignee filter:**
```bash
attio tasks list --not-completed --assignee <actor_id> --json
```

**With object type filter:**
```bash
attio tasks list --not-completed --linked-object deals --json
```

**Combined:**
```bash
attio tasks list --not-completed --linked-object deals --assignee <actor_id> --json
```

### Step 2 — Filter to overdue (client-side)

Parse the JSON response and keep only tasks where `deadline_at` is non-null and `deadline_at < now()` in UTC.

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
overdue = [
    t for t in tasks["data"]
    if t.get("deadline_at")
    and datetime.fromisoformat(t["deadline_at"].replace("Z", "+00:00")) < now
]
```

Sort ascending by `deadline_at` so the oldest overdue tasks surface first.

### Step 3 — Format for review

Group by linked object type, then by record name within each group. See Output Format section for exact display spec.

### Step 4 — Present for action

For each task, prompt the user to choose an action:

```
[c] Mark complete
[s] Snooze (set new deadline)
[n] Add note
[skip] Skip (leave as-is)
```

Loop through tasks in order. After all tasks are processed, print a summary: N marked complete, N snoozed, N skipped.

---

## Output Format

Tasks are displayed grouped by linked object type, then by record. Within a record, tasks are sorted oldest deadline first.

```
OVERDUE TASKS — 2026-03-31
─────────────────────────────────────────────────────
DEALS (3 tasks)

  Acme Corp — Series B Expansion
    [abc-123]  Follow up on pricing deck          Overdue 3d  Assignee: mitch@leadgrow.ai
    [abc-124]  Send contract draft               Overdue 1d  Assignee: mitch@leadgrow.ai

  Tensorlake — Q2 Renewal
    [abc-125]  Confirm technical requirements    Overdue 5d  Assignee: unassigned

PEOPLE (1 task)

  Jordan Lee (VP Sales, Boundless)
    [abc-126]  Schedule intro call               Overdue 7d  Assignee: mitch@leadgrow.ai

COMPANIES (0 tasks)

─────────────────────────────────────────────────────
TOTAL: 4 overdue tasks
```

**Field definitions:**

| Field | Source | Display |
|-------|--------|---------|
| Task ID | `task.id.task_id` | Shown in brackets for action targeting |
| Content | `task.content` | Full text, truncated at 60 chars with `…` if longer |
| Overdue duration | `now - deadline_at` | Human-readable: `Overdue 3d`, `Overdue 14h` |
| Assignee | `task.assignees[0].referenced_actor_id` | Resolved to email/name via `attio workspace members`; show `unassigned` if empty |
| Linked record name | `task.linked_records[0].target_record_id` | Resolved via `attio records get` on the linked object |

Assignee resolution and record name resolution should be cached in-memory per session to avoid redundant API calls.

---

## Actions Available

### Mark complete

```bash
attio tasks update <task_id> --completed
```

### Update deadline (snooze)

Prompt for new deadline. Accept natural input (`+3d`, `+1w`, specific date `2026-04-07`) and convert to ISO 8601.

```bash
attio tasks update <task_id> --deadline 2026-04-07T00:00:00.000Z
```

### Add a note

Notes attach to the linked record, not to the task directly. Pull `target_object` and `target_record_id` from `task.linked_records[0]`.

```bash
attio notes create \
  --parent-object deals \
  --parent-record-id <record_id> \
  --title "Task follow-up — 2026-03-31" \
  --content "Snoozed: [reason entered by user]"
```

If a task has no linked record, skip note creation and warn the user.

---

## Error Handling

### No overdue tasks

```
All tasks are on track. No overdue items as of 2026-03-31 09:00 UTC.
```

Exit cleanly. No action required.

### API authentication failure

```
Error: ATTIO_API_KEY not set or invalid. Run `attio config set api-key <key>` to configure.
```

Halt immediately. Do not attempt partial execution.

### Task has no linked record

Display the task without a record header. Use `[No linked record]` as the group label. Note creation is skipped for these tasks; offer only mark-complete or snooze.

### Deadline parse failure

If `deadline_at` is present but unparseable, log a warning and skip that task:
```
Warning: Could not parse deadline for task abc-999 — skipping.
```

### Rate limiting (429)

The attio-cli client handles retries via tenacity. The skill does not need additional retry logic. If retries are exhausted, surface the error and exit.

---

## Example Usage

### Morning review, all overdue tasks

```bash
# Pull and display all overdue tasks across the workspace
attio tasks list --not-completed --json | python -m attio_workflows.overdue_tasks
```

### My tasks only, deals pipeline

```bash
# Surface only deals-linked overdue tasks assigned to you
ACTOR_ID=$(attio workspace members --json | jq -r '.data[] | select(.email=="mitch@leadgrow.ai") | .actor_id')

attio tasks list \
  --not-completed \
  --linked-object deals \
  --assignee "$ACTOR_ID" \
  --json \
| python -m attio_workflows.overdue_tasks
```

---

## CLI Commands Used

| Command | Purpose |
|---------|---------|
| `attio tasks list --not-completed --json` | Fetch all incomplete tasks |
| `attio tasks list --not-completed --linked-object <slug> --json` | Filter by object type |
| `attio tasks list --not-completed --assignee <actor_id> --json` | Filter by assignee |
| `attio tasks update <task_id> --completed` | Mark a task complete |
| `attio tasks update <task_id> --deadline <iso8601>` | Push deadline (snooze) |
| `attio notes create --parent-object <slug> --parent-record-id <id> --title <t> --content <c>` | Add a note to the linked record |
| `attio workspace members --json` | Resolve actor IDs to names/emails for display |

---

## Implementation Notes for Developer

1. **Deadline filtering is client-side.** The Attio v2 tasks endpoint does not expose a `deadline_before` query parameter. You must fetch all incomplete tasks and filter in Python.

2. **Linked record name resolution is N+1 by default.** Cache all record fetches in a dict keyed by `(target_object, target_record_id)` to avoid hammering the API when multiple tasks link to the same record.

3. **Assignee resolution.** Call `attio workspace members --json` once at session start and build a lookup dict. The `referenced_actor_id` in task assignees maps to the member's `actor_id` field.

4. **Interactive loop.** Use `click.prompt()` or `prompt_toolkit` for the per-task action prompt. The loop must be skippable (Ctrl+C exits gracefully with a summary of what was processed before exit).

5. **Scheduled (non-interactive) mode.** When piped or run with `--no-interact`, skip the action loop and output a formatted digest to stdout. This lets the automation layer format it as a Telegram message or write it to a daily file.

6. **Object type display order.** Always show `DEALS` first, then `PEOPLE`, then `COMPANIES`, then any other object types alphabetically. Deals are highest priority in a GTM pipeline context.
