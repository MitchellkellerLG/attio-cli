# Skills Audit — 2026-04-01

Cross-reference of all 4 GTM skills in `skills/` against the actual attio-cli source in `agent-harness/cli_anything/attio/`.

---

## post-call-followup

### Broken command references

**1. `attio people search --email "..." --json` — flag does not exist**

Skill says (Step 1):
```bash
attio people search --email "sarah@acme.com" --json
```

CLI source (`records.py`, line 162–169): The `search` command for all object groups (including `people`) takes a single positional `query` argument only. Signature:
```python
@group.command("search")
@click.argument("query")
@click.option("--limit", ...)
@click.option("--json", ...)
```

There is no `--email` flag. The correct call is:
```bash
attio people search "sarah@acme.com" --json
```

**2. `attio people get --id "..." --json` — flag name is wrong**

Skill says (Step 1):
```bash
attio people get --id "rec_01abc123" --json
```

CLI source (`records.py`, line 91–98): The `get` command uses a positional `record_id` argument, not an `--id` flag:
```python
@group.command("get")
@click.argument("record_id")
```

The correct call is:
```bash
attio people get rec_01abc123 --json
```

**3. `attio notes list --record-id "..." --limit 5 --json` — flag name wrong, `--limit` doesn't exist**

Skill says (Step 2):
```bash
attio notes list --record-id "<record_id>" --limit 5 --json
```

CLI source (`notes.py`, line 53–69): The `notes list` command uses `--parent-record-id`, not `--record-id`. There is also no `--limit` flag on `notes list`:
```python
@notes_group.command("list")
@click.option("--parent-object", ...)
@click.option("--parent-record-id", ...)
@click.option("--json", ...)
```

The correct call is:
```bash
attio notes list --parent-object people --parent-record-id "<record_id>" --json
```

**4. `attio tasks create --record-id "..." --title "..." --due-date "..." --json` — three wrong flags**

Skill says (Output section):
```bash
attio tasks create \
  --record-id "<record_id>" \
  --title "Send follow-up email to [First Name]" \
  --due-date "<24h from now, ISO 8601>" \
  --json
```

CLI source (`tasks.py`, line 15–55): `tasks create` has no `--record-id`, `--title`, or `--due-date` flags. The actual flags are:
- `--content` (required) — not `--title`
- `--deadline` — not `--due-date`
- `--linked-record` (JSON string, repeatable) — not `--record-id`

The correct call is:
```bash
attio tasks create \
  --content "Send follow-up email to [First Name]" \
  --deadline "<24h from now, ISO 8601>" \
  --linked-record '{"target_object":"people","target_record_id":"<record_id>"}' \
  --json
```

### Missing CLI coverage

**5. `attio notes list --limit N` — no limit on notes list**

The skill uses `--limit 5` to cap notes fetched per contact. `notes list` has no `--limit` flag. The full note list is always returned. For contacts with long histories this is fine (unlikely to be huge), but the skill implies limit control that doesn't exist. Claude must truncate the returned list client-side if needed.

### Logic gaps

**6. `note.parent_record_id` field assumed — actual field path unknown from source alone**

Step 0 (bulk mode) filters notes by `note.parent_record_id` to group by contact. The CLI source doesn't expose the JSON shape of a note response — that's the Attio API's schema. If the actual field is nested (e.g., `note.parent_record.record_id`), the bulk grouping logic silently produces an empty queue. No guard exists for this.

**7. Bulk mode assumes `note.title` is always populated**

Step 0 filters by `note.title contains "call"`. Notes created programmatically or by some integrations may have no title (null or empty string). The filter logic will silently exclude them. No fallback or null check is documented.

**8. "Multiple contacts match" ambiguity has no fallback in bulk mode**

In bulk mode, each contact is resolved via their `parent_record_id` from the note — no search is needed. But Step 1 still describes the "multiple matches" failure state, which only applies to single-contact mode. In bulk mode, there can never be a search-result ambiguity. The skill mixes these two modes' error handling.

**9. `attio-cli Commands Used` table is inconsistent with Step 2**

The table at the bottom lists:
```
attio notes list --record-id "..." --limit 5 --json
```
This matches the broken command in Step 2, but both are wrong (should be `--parent-record-id`, no `--limit`). Two places need fixing, not one.

---

## overdue-follow-up

### Broken command references

**10. `attio tasks list --not-completed --linked-object deals --json` — flag name wrong**

Skill says (Step 1):
```bash
attio tasks list --not-completed --linked-object deals --json
```

CLI source (`tasks.py`, line 68–91): The completion filter is a boolean pair: `--completed/--not-completed` maps to `is_completed`. This part is correct. However `--linked-object` is valid (`linked_object` parameter exists). This command is actually fine.

Wait — re-checking: the CLI does have `--linked-object` and `--not-completed`. This command is correct.

**11. `attio tasks update <task_id> --deadline <iso8601>` — flag name wrong**

Skill says (User Actions — Approve):
```bash
attio tasks update <task_id> --deadline <now+7d in ISO 8601>
```

CLI source (`tasks.py`, line 94–117): The flag is `--deadline` mapped to `deadline_at`. The flag name `--deadline` IS correct. This one is fine.

**12. `attio tasks update <task_id> --completed` — flag name wrong**

Skill says (User Actions — c):
```bash
attio tasks update <task_id> --completed
```

CLI source (`tasks.py`, line 98–99):
```python
@click.option("--completed/--not-completed", "is_completed", default=None, ...)
```

The flag `--completed` IS a valid side of the boolean pair. This is correct.

**13. `attio records get --object people --record-id <id> --json` — positional not flag**

Skill says (Step 2):
```bash
attio records get --object people --record-id <target_record_id> --json
```

CLI source (`records.py`, line 215–225): `records get` takes `object_slug` and `record_id` as positional arguments:
```python
@records_group.command("get")
@click.argument("object_slug")
@click.argument("record_id")
```

The correct call is:
```bash
attio records get people <target_record_id> --json
```

**14. `attio notes list --parent-object people --parent-record-id <id> --json` — CORRECT**

CLI source (`notes.py`, line 53–69): Flags `--parent-object` and `--parent-record-id` both exist. This command is correct. No issue.

**15. `attio notes create --parent-object <slug> --parent-record-id <id> --title <t> --content <c>` — CORRECT**

CLI source (`notes.py`, line 14–40): All flags exist: `--parent-object`, `--parent-record-id`, `--title`, `--content`. This command is correct.

**16. `attio workspace members --json` — subcommand name wrong**

Skill says (Commands table):
```
attio workspace members --json
```

CLI source (`workspace.py`, line 13–20): The command is registered as `workspace_group` with subcommand `members`. So the correct call is:
```bash
attio workspace members --json
```

This IS correct. The `workspace_group` is registered in `attio_cli.py` line 98.

### Missing CLI coverage

**17. `--assignee <actor_id>` filter on tasks list — exists but skill description is misleading**

Skill says to use `attio workspace members` to get actor IDs for the `--assignee` filter. The CLI tasks list does accept `--assignee` (`tasks.py` line 71). However the skill says "Get IDs via `attio workspace members`" — the `workspace members` output format is not defined in the source we can see, so the mapping from members output to an actor ID suitable for `--assignee` is unverified.

### Logic gaps

**18. `linked_records[0]` assumed to always exist — no null guard**

Step 2: "For each overdue task, extract `linked_records[0]`..."

The Attio API can return tasks with no linked records (orphaned tasks). If `linked_records` is an empty array, `linked_records[0]` raises an IndexError or returns None. The skill has no guard for this case and no documented behavior ("skip the task" vs "warn and skip").

**19. Deal-linked tasks: "associated_people" field name is assumed, not verified**

Implementation Note 3: "Fetch the deal record first, then extract associated person IDs (`associated_people` attribute)."

The actual field name on Attio deal records for linked contacts is workspace-specific (depends on how the object was configured). `associated_people` is an assumption. If the field is named differently in the workspace (e.g. `people`, `contacts`), the double-resolution logic silently returns no contact and the follow-up is generated with no name/email.

**20. Client-side deadline filtering claims API limitation that may no longer be true**

The skill states: "The Attio v2 tasks endpoint does not support `deadline_before` as a query parameter." This was accurate at time of writing but the Attio API is actively developed. If they've since added this parameter, the fetch-all-then-filter-client-side approach wastes API calls. Low urgency but worth verifying against current API docs before treating it as permanent.

---

## lead-nurture

### Broken command references

**21. `attio lists entries list <list_id> --json` — wrong subcommand group**

Skill says (Step 2):
```bash
attio lists entries list <list_id> --json
```

CLI source: There is no `entries` subcommand under `lists`. Entries are managed under a separate top-level group:
```python
# attio_cli.py line 94
cli.add_command(entries_group)  # registered as "entries"
```

The `entries_group` (from `entries.py`) is a top-level command, not a subcommand of `lists`. The correct call is:
```bash
attio entries list <list_id> --json
```

This is probably the highest-impact broken command in all 4 skills — it's the core data-pull step for this entire workflow.

**22. `attio tasks list --linked-object people --linked-record-id <id> --not-completed --json` — CORRECT**

CLI source (`tasks.py`, line 68–91): `--linked-object`, `--linked-record-id`, and `--not-completed` all exist. This command is correct.

**23. `attio tasks create --linked-object <obj> --linked-record-id <id> --content <text> --deadline <iso8601>` — flags wrong**

Skill says (Approve section):
```bash
attio tasks create \
  --linked-object people \
  --linked-record-id <record_id> \
  --content "Nurture message sent..." \
  --deadline <today+5d in ISO8601>
```

CLI source (`tasks.py`, line 15–55): `tasks create` has no `--linked-object` or `--linked-record-id` flags. Linked records are specified as JSON via `--linked-record`:
```python
@click.option("--linked-record", "linked_records", multiple=True,
              help='Linked record as JSON: \'{"target_object":"people","target_record_id":"..."}\'. Repeatable.')
```

The correct call is:
```bash
attio tasks create \
  --content "Nurture message sent..." \
  --deadline <today+5d in ISO8601> \
  --linked-record '{"target_object":"people","target_record_id":"<record_id>"}' \
  --json
```

**24. `attio lists entries delete <list_id> <entry_id>` — wrong subcommand group**

Skill says (Remove from list):
```bash
attio lists entries delete <list_id> <entry_id>
```

Same issue as #21. There's no `entries` under `lists`. The correct call is:
```bash
attio entries delete <list_id> <entry_id> --yes
```

Note also that `entries delete` requires `--yes` to skip the confirmation prompt, or it will block waiting for interactive input — which will hang in agent execution.

**25. `attio records get --object <obj> --record-id <id> --json` — same positional error as #13**

Skill says (Step 3):
```bash
attio records get --object people --record-id <record_id> --json
```

Should be:
```bash
attio records get people <record_id> --json
```

**26. `attio workflow lead-nurture ...` — does not exist**

The Example Invocation section shows:
```bash
attio workflow lead-nurture --list "Nurture"
attio workflow lead-nurture --list "Interested - No Response" --days 14
```

There is no `workflow` subcommand in the CLI. These are skill-invocation examples, not actual CLI commands. This is documentation confusion — these look like executable commands but they're not. Anyone reading the skill file bottom-up will be confused.

### Missing CLI coverage

**27. No `--limit` flag on `notes list`**

Skill (Step 3 via Step 4 logic) assumes pulling notes per contact is bounded. `notes list` returns all notes for a record with no limit. For contacts with many notes, this is more data than needed. No limit control exists.

**28. `attio lists entries list` has no `--parent-record-id` filter**

Entries are fetched for an entire list at once. There's no CLI-level filter to get entries for a specific record. If a contact appears on multiple lists and you're trying to find their specific entry_id for removal, you must fetch all entries and filter client-side. The skill doesn't document this.

### Logic gaps

**29. `r.get("job_title")` field name assumption**

Step 5 (persona filter):
```python
stale = [r for r in stale if keyword in (r.get("job_title") or "").lower()]
```

The Attio API returns attribute values nested under `values` (e.g., `record["data"]["values"]["job_title"]`). The field access `r.get("job_title")` assumes a flat structure. If the actual response is nested, this filter silently passes all records through (no one gets filtered out).

**30. `last_activity` returning `None` for records with no notes/tasks — edge case mis-handled**

Step 4 Python snippet:
```python
def last_activity(record_id: str) -> datetime | None:
    ...
    return max(timestamps) if timestamps else None
```

Then in the filter:
```python
stale = [r for r in records if (last_activity(r["id"]) or datetime.min.replace(tzinfo=timezone.utc)) < cutoff]
```

Records with no history get `datetime.min` (year 1), which IS less than cutoff — so they're always included. This is the intended behavior (no history = include). But `datetime.min` with `tzinfo=timezone.utc` may raise in older Python implementations since `datetime.min` is naive. The safer pattern is `datetime(1, 1, 1, tzinfo=timezone.utc)`. Minor but worth noting.

**31. `list_entry.updated_at` used as activity signal — not the same as contact activity**

Step 4: The inactivity check includes `list_entry.updated_at`. This field updates when the entry's stage or attributes change in the list — not when the contact was actually touched. A stage change by Mitch (e.g., dragging a card) resets this timer without any actual outreach happening. This can cause contacts to be excluded from the nurture queue even though no one reached out to them.

---

## deal-next-step

### Broken command references

**32. `attio deals search "<deal_name>" --json --limit 5` — query is positional, not a flag**

Skill says (Step 1):
```bash
attio deals search "<deal_name>" --json --limit 5
```

CLI source (`records.py`, line 161–169): `search` takes `query` as a positional argument. The `--limit` flag also exists. This command is actually correct — `query` is positional so this works. Fine.

**33. `attio people search "<email>" --json --limit 3` — correct**

Same structure as above. The positional `query` accepts an email string. Correct.

**34. `attio records list deals --filter '{"linked_record": ...}' --json` — filter syntax unverified**

Skill says (Step 1, email-to-deal lookup):
```bash
attio records list deals --filter '{"linked_record": {"target_object": "people", "target_record_id": "<PERSON_ID>"}}' --json
```

CLI source (`records.py`, line 189–212): `records list` accepts `--filter` with JSON, key=value, or @file formats. The JSON body is passed directly to the Attio API. Whether `linked_record` is a valid Attio v2 filter key for deals is an API question, not a CLI question — but the CLI will accept and pass it. If Attio's API doesn't support this filter key, the command returns unfiltered results or an API error. The skill doesn't document a fallback if zero results are returned from this filter.

**35. `attio records get deals <DEAL_ID> --json` — CORRECT**

CLI source (`records.py`, line 215–225): `records get` takes `object_slug` and `record_id` as positional arguments. This syntax is correct.

**36. `attio records get people <PERSON_ID> --json` and `attio records get companies <COMPANY_ID> --json` — CORRECT**

Same pattern. Both correct.

**37. `attio notes list --parent-object deals --parent-record-id <DEAL_ID> --json` — CORRECT**

CLI source (`notes.py`, line 53–69): Correct flags. Fine.

**38. `attio tasks list --not-completed --linked-object deals --json` — CORRECT**

CLI source (`tasks.py`, line 68–91): Correct. Fine.

**39. `attio tasks create --content <text> --deadline <iso8601> --linked-record <json> --json` — CORRECT**

CLI source (`tasks.py`, line 15–55): This is the correct form. The skill has it right.

**40. `attio records update deals <DEAL_ID> --values <json> --json` — CORRECT**

CLI source (`records.py`, line 245–262): `records update` takes `object_slug` and `record_id` as positional arguments, with `--values` flag. Correct.

### Missing CLI coverage

**41. No `attio deals search` exists as distinct command — uses `attio deals search` via the shared factory**

This works fine — `deals` is built by `_make_record_group` which includes `search`. But the skill references `attio deals search` while also referencing `attio records list deals --filter`. These are two different ways to find a deal. The skill doesn't clarify when to use which. For name-based lookup, `attio deals search "<name>"` is simpler. For linked-record lookup, `attio records list deals --filter` is needed but its filter syntax is unverified (see #34).

**42. No `attio tasks list` filter for a specific deal — must filter client-side**

Step 5:
```bash
attio tasks list --not-completed --linked-object deals --json
```
"Filter client-side to tasks where `linked_records[].target_record_id == DEAL_ID`."

This is correct — the CLI supports `--linked-object` but not filtering by a specific record ID when combined with `--linked-object`. Wait — checking `tasks.py` line 71: `--linked-record-id` exists. So you CAN filter directly:
```bash
attio tasks list --not-completed --linked-object deals --linked-record-id <DEAL_ID> --json
```

The skill is doing unnecessary client-side filtering when it could pass `--linked-record-id` directly to the CLI. This makes the data pull heavier than it needs to be (fetches all deal tasks instead of just the target deal's tasks).

### Logic gaps

**43. `linked_contacts` field name assumed — same risk as #19**

Step 2 extracts `linked_contacts` from the deal record. The actual Attio API field name for contacts linked to a deal is workspace-specific. If the field is named `people` or `contacts` instead of `linked_contacts`, the contact resolution in Step 3 silently returns nothing and the skill proceeds with no contact name, email, or title.

**44. `stage_entered_at` field assumed — not a standard Attio API field**

Step 2 extracts `stage_entered_at` to calculate `days_in_stage`. Attio's v2 API does not expose a `stage_entered_at` timestamp as a standard record attribute. Stage tracking (when a record entered a stage) is managed through list entry history, not a record attribute. If this field doesn't exist in the response, `days_in_stage` calculation fails and the entire Step 7 time-in-stage diagnosis is broken.

**45. Deal-to-people lookup via filter — no fallback if filter returns 0 results**

Step 1: If the email-to-deal lookup via `--filter '{"linked_record": ...}'` returns 0 results (either because the filter isn't supported or the deal isn't linked to that person in Attio), the skill halts with "No deal found." But the real problem might be a filter syntax issue, not an absent deal. The error message should distinguish between "deal not found" and "filter may have failed."

---

## Priority Fix List

Ranked by: will this break the skill entirely (P0) or cause wrong behavior (P1) or is it a gap (P2)?

| # | Issue | Skill | Severity | Description |
|---|-------|-------|----------|-------------|
| 1 | `attio lists entries list` → should be `attio entries list` | lead-nurture | **P0** | Core data pull for entire workflow is under wrong command group. Will error on every run. |
| 2 | `attio lists entries delete` → should be `attio entries delete` | lead-nurture | **P0** | Remove-from-list action completely broken. Same root cause as #1. |
| 3 | `attio tasks create --record-id/--title/--due-date` → `--linked-record/--content/--deadline` | post-call-followup | **P0** | Task creation (the final deliverable of the skill) will fail every time with three wrong flags. |
| 4 | `attio tasks create --linked-object/--linked-record-id` → `--linked-record <json>` | lead-nurture | **P0** | Task creation after approval is broken. Same root cause — wrong linked-record interface. |
| 5 | `attio notes list --record-id/--limit` → `--parent-record-id`, no `--limit` | post-call-followup | **P0** | Note pull in Step 2 fails. Wrong flag name will error; `--limit` silently ignored. |
| 6 | `attio people get --id` → positional argument | post-call-followup | **P0** | Record fetch by ID fails whenever Mitch provides an Attio record ID directly. |
| 7 | `attio people search --email` → positional argument | post-call-followup | **P0** | Email-based contact lookup fails every time. |
| 8 | `attio records get --object/--record-id` → positional arguments | overdue-follow-up, lead-nurture | **P0** | Record fetch in Step 2 of overdue-follow-up and Step 3 of lead-nurture broken. |
| 9 | `stage_entered_at` field does not exist in Attio v2 API | deal-next-step | **P1** | Days-in-stage diagnosis (Step 7) produces errors or zeros. Kills the main analytical value of the skill. |
| 10 | `linked_records[0]` no null guard | overdue-follow-up | **P1** | Orphaned tasks (no linked record) crash the loop with an IndexError, stopping the entire session. |
| 11 | `attio tasks list` with both `--linked-object deals` and no `--linked-record-id` | deal-next-step | **P2** | Fetches ALL deal tasks then filters client-side, when `--linked-record-id` flag exists and would do it server-side. Wastes API calls on large pipelines. |
| 12 | `attio workflow lead-nurture` invocation examples | lead-nurture | **P2** | Non-existent CLI command in example invocations. Confusing to anyone reading the skill as a reference. |
