---
name: log-call
description: >
  Log a sales call to Attio in one workflow. Finds or creates the contact
  (person) record, adds a structured note with AI-written call summary, and
  creates a follow-up task with a deadline. Use after any prospect or client call.
version: 0.1.0
maturity: draft
triggers:
  - log a call
  - log sales call
  - record call notes in attio
  - add follow-up task after call
  - sync call to crm
  - log meeting to attio
---

# Skill: log-call

Log a sales call to Attio. One workflow: find-or-create contact, write structured note, create follow-up task.

---

## Purpose

After a sales call with a prospect or client, Mitch (or an agent) dumps raw call notes and a follow-up action. This skill takes that input, writes a clean structured note, and writes the whole thing to Attio — contact record, note, and task — in a single operation.

No manual CRM entry. No lost follow-ups.

---

## Trigger

Any of the following:

- Mitch says "log the call with [name]" and provides notes
- An agent is handed a Fireflies transcript and told to log it
- Post-call workflow drops inputs into this skill automatically

---

## Inputs

| Input | Required | Type | Notes |
|-------|----------|------|-------|
| `contact_name` | If no email | string | Full name. Used for person lookup and record creation. |
| `contact_email` | If no name | string | Preferred for lookup — unambiguous match via `email_addresses` attribute. |
| `company_name` | No | string | Used to set/confirm the person's company in Attio. |
| `call_summary` | Yes | string | Freeform — raw bullets, transcript excerpt, or prose. AI rewrites this into the note. |
| `follow_up_action` | Yes | string | What needs to happen next. Becomes the task content. |
| `deadline` | Yes | string | ISO 8601 date or natural language (e.g. "April 7", "next Tuesday"). Claude converts to ISO 8601 before passing to CLI. |
| `duration_minutes` | No | integer | Call length in minutes. Included in note if provided. |

---

## Steps

Exact execution sequence. Each step depends on the previous.

### Step 1 — Find or create the person record

**Goal:** Get a `person_record_id` to attach the note and task to.

**Preferred path (email provided):**

```bash
# Assert the person — creates if not found, returns existing if found
attio people assert \
  --matching-attribute email_addresses \
  --values '{"email_addresses": [{"email_address": "<email>"}], "name": [{"full_name": "<name>"}]}' \
  --json
```

Extract `data.id.record_id` from the response. This is `PERSON_ID`.

**Fallback (name only, no email):**

```bash
attio people search "<name>" --json --limit 5
```

If exactly one result is returned, use its `id.record_id` as `PERSON_ID`. If zero or multiple results, escalate to error handling (see below).

**If company name is provided** and the record is newly created, also upsert the company and link it:

```bash
attio companies assert \
  --matching-attribute domains \
  --values '{"name": [{"value": "<company_name>"}]}' \
  --json
# Then update the person record to link the company if needed.
```

---

### Step 2 — Write the structured note (AI step)

Claude takes the raw `call_summary` input and produces a formatted note body. See [Note Format](#note-format) section below.

The note is a string. Pass it directly to the CLI.

```bash
attio notes create \
  --parent-object people \
  --parent-record-id "<PERSON_ID>" \
  --title "Call — <YYYY-MM-DD>" \
  --content "<formatted_note_body>" \
  --format plaintext \
  --json
```

Extract `data.id.note_id` from the response. This is `NOTE_ID`.

---

### Step 3 — Create the follow-up task

```bash
attio tasks create \
  --content "<follow_up_action>" \
  --deadline "<ISO_8601_deadline>" \
  --linked-record '{"target_object": "people", "target_record_id": "<PERSON_ID>"}' \
  --json
```

Extract `data.id.task_id` from the response. This is `TASK_ID`.

---

## Note Format

Claude writes this. The template is:

```
Date: YYYY-MM-DD
Duration: X min  [omit if not provided]

## Key Points
- [bullet from call summary]
- [bullet from call summary]
- ...

## Signals
- [any buying signals, objections, pain points Claude identifies from the summary]

## Next Steps
- [follow_up_action as stated]
- [any additional next steps Claude infers from the summary]
```

Rules for note writing:

- Extract only what was stated or clearly implied. No fabrication.
- If the input is a Fireflies transcript, pull direct quotes for signals when they're strong.
- Keep it tight. 80/20 — the one paragraph a future reader actually needs.
- "Key Points" = what was discussed. "Signals" = prospect's state (interest, objections, timeline). "Next Steps" = what happens now.
- Use plaintext. No markdown decorators that won't render in Attio.

---

## Output

On success, print a confirmation block:

```
Call logged to Attio.

Contact:  <name> (<email if available>)
Record:   https://app.attio.com/records/people/<PERSON_ID>
Note ID:  <NOTE_ID>
Task:     "<follow_up_action>" due <deadline>
Task ID:  <TASK_ID>
```

When running in agent mode (`--json` on all commands), the final confirmation should be a JSON object:

```json
{
  "status": "success",
  "person_record_id": "<PERSON_ID>",
  "note_id": "<NOTE_ID>",
  "task_id": "<TASK_ID>",
  "attio_record_url": "https://app.attio.com/records/people/<PERSON_ID>"
}
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No email AND no name provided | Abort immediately. Return error: "Need at least a name or email to find the contact." |
| Name search returns 0 results, no email | Abort. Return error: "No person found for '<name>'. Provide an email to create a new record." |
| Name search returns 2+ results | Abort. Return error: "Multiple people matched '<name>'. Provide an email to disambiguate." |
| `notes create` fails | Log the error. Do NOT create the task. Return the person record ID so the note can be retried without creating a duplicate person. |
| `tasks create` fails | Log the error. Note is already created — return note ID and the failure. Do not retry the note. |
| Invalid deadline format | Claude converts natural language to ISO 8601 before calling the CLI. If conversion is ambiguous, ask the user to clarify before proceeding. |
| API key missing | CLI exits with code 4. Surface this as "Attio auth not configured. Run: `attio config set api-key <key>`" |

---

## Example Usage

### Example 1 — Prospect discovery call, email available

Input:
```
contact_email: james.wu@storylane.io
contact_name: James Wu
company_name: Storylane
duration_minutes: 28
follow_up_action: Send case study deck + book a second call with their head of sales
deadline: April 7, 2026
call_summary: |
  James is head of growth at Storylane. They run outbound today but it's all spray and pray.
  No ICP definition beyond "mid-market SaaS." Interested in what we do with Clay for enrichment.
  Asked about our pricing — I said we'd cover in a follow-up. He mentioned their Q2 starts May 1
  so timing is good. Pain: low reply rates, team doesn't know why emails aren't converting.
  Not running any LinkedIn. Warm to the idea of a quick win test.
```

Claude constructs the note, runs three commands (assert person, create note, create task), and outputs:

```
Call logged to Attio.

Contact:  James Wu (james.wu@storylane.io)
Record:   https://app.attio.com/records/people/rec_abc123
Note ID:  note_xyz789
Task:     "Send case study deck + book a second call with their head of sales" due 2026-04-07
Task ID:  task_def456
```

---

### Example 2 — Existing client check-in, name only (no email)

Input:
```
contact_name: Sarah Okonkwo
follow_up_action: Update targeting doc with new segment they identified
deadline: next Monday
call_summary: |
  Weekly check-in with Sarah. Campaign is 3 weeks in. Reply rate sitting at 6.8% which
  is above benchmark. They want to add a new segment: ops leaders at logistics companies
  20-200 employees. Need to update the targeting doc and spin up a new sequence variant.
  She's happy with pace. No blockers.
```

Claude searches for "Sarah Okonkwo", finds one result, uses that record ID. Runs create note + create task. Outputs confirmation.

If two Sarah Okonkwos are found, returns:

```
Error: Multiple people matched 'Sarah Okonkwo'. Provide an email to disambiguate.
```

---

## CLI Commands Used

All commands from the `attio` CLI. In execution order:

| Command | Purpose |
|---------|---------|
| `attio people assert --matching-attribute email_addresses --values <json> --json` | Upsert person by email (preferred path) |
| `attio people search <name> --json --limit 5` | Fuzzy search by name (fallback path) |
| `attio companies assert --matching-attribute domains --values <json> --json` | Upsert company if provided (optional) |
| `attio notes create --parent-object people --parent-record-id <id> --title <t> --content <c> --format plaintext --json` | Create structured call note |
| `attio tasks create --content <text> --deadline <iso8601> --linked-record <json> --json` | Create follow-up task linked to person |

Key flag details:

- `people assert` uses `--matching-attribute email_addresses`. The values JSON must use the `email_addresses` key with an array containing `{"email_address": "..."}`.
- `tasks create --linked-record` takes a JSON string: `'{"target_object": "people", "target_record_id": "<id>"}'`
- `tasks create --deadline` must be ISO 8601. Example: `2026-04-07T00:00:00.000Z`. Claude converts natural language to this format before the CLI call.
- `notes create --format` accepts `plaintext` or `markdown`. Use `plaintext` unless you know the Attio workspace renders markdown in notes.
- All commands use `--json` for machine-readable output in agent mode.

---

## AI Role

Clear division of labor:

| Responsibility | Claude | CLI |
|----------------|--------|-----|
| Parse raw call notes into structured format | Yes | No |
| Write the note body (Key Points, Signals, Next Steps) | Yes | No |
| Convert natural language deadlines to ISO 8601 | Yes | No |
| Decide whether to search or assert based on inputs | Yes | No |
| Execute API calls | No | Yes |
| Handle auth, retries, rate limiting | No | Yes |
| Return machine-readable output | No | Yes (--json) |
| Validate JSON passed to --values / --linked-record | Claude builds it, CLI validates it | Yes |

Claude touches no API directly. Every write goes through the CLI. Claude's job is input interpretation and note authorship. The CLI's job is execution and error surfacing.
