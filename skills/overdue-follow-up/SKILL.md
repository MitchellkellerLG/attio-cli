---
name: overdue-follow-up
description: >
  Pull all overdue Attio tasks, fetch each contact's full note history, generate a
  personalized follow-up message in LeadGrow voice, and present one at a time for
  Mitch to approve, edit, skip, or mark complete. On approval, updates the task
  deadline and optionally queues the message to EmailBison. Use this during morning
  pipeline review, weekly pipeline cleanup, or any time you hear "who have I been
  ghosting" or "what follow-ups are overdue."
version: 0.1.0
triggers:
  - overdue follow-ups
  - who have I been ghosting
  - follow-up pipeline
  - pipeline cleanup
  - what follow-ups do I owe
  - morning pipeline review
  - write follow-up messages
  - draft follow-ups for overdue tasks
  - who needs a follow-up
  - overdue outreach
  - contact follow-up queue
---

# Skill: `overdue-follow-up`

**Project:** attio-cli
**Layer:** Workflow skill — multi-command orchestration + AI copy generation
**Audience:** Claude executing this interactively with Mitch in a Claude Code session

---

## When to Use

Run this skill when:

- Starting the day and want to clear follow-up debt before new work enters
- End of week pipeline cleanup — who fell through the cracks
- Mitch says anything like "who have I been ghosting" or "what follow-ups are overdue"
- There's a batch of deals or prospects that haven't moved and you want to generate outreach before the trail goes cold

**This is not a fire-and-forget automation.** Every message requires Mitch's explicit approval before anything sends. Claude generates the copy; Mitch decides what goes out.

**Related skill:** `overdue-tasks` (docs/workflows/skill-overdue-tasks.md) handles hygiene-only triage (mark complete / snooze / note). Use that when you just want to clear the task list. Use THIS skill when you want to generate and send follow-up messages.

---

## Inputs

All filters are optional. No flags = full overdue task list across all contacts.

| Flag | Type | Description |
|------|------|-------------|
| `--object <slug>` | string | Limit to tasks linked to a specific object: `people`, `deals`, `companies`. Default: all. |
| `--assignee <actor_id>` | string | Filter to tasks assigned to a specific workspace member. Get IDs via `attio workspace members`. |
| `--limit <n>` | int | Cap to N contacts. Useful if the backlog is large — start with `--limit 5` for the highest-priority batch. |
| `--queue-approved` | flag | When present, approved messages are queued to EmailBison as new campaigns or reply drafts. When absent, approved messages are printed to screen only and Mitch sends manually. |

---

## What Claude Does — Step by Step

### Step 1 — Pull all overdue tasks

```bash
attio tasks list --not-completed --json
```

Filter client-side to tasks where `deadline_at` is non-null and `deadline_at < now()` in UTC. Sort ascending by `deadline_at` (oldest overdue first — these are the most at-risk).

Apply any `--object` or `--assignee` flags at query time:

```bash
# Deals only
attio tasks list --not-completed --linked-object deals --json

# Specific assignee
attio tasks list --not-completed --assignee <actor_id> --json
```

**If zero overdue tasks:** Print `No overdue tasks. Pipeline is clean.` and exit.

### Step 2 — Resolve linked contacts

For each overdue task, extract `linked_records[0]` and fetch the full contact record:

```bash
# For a person
attio records get --object people --record-id <target_record_id> --json

# For a deal (fetch the deal, then resolve associated people)
attio records get --object deals --record-id <target_record_id> --json
```

Cache all record fetches in-memory by `(target_object, target_record_id)` to avoid redundant API calls when multiple tasks link to the same record.

Extract from the record: name, company, title/role, email address, any custom fields relevant to the relationship (deal stage, industry, last campaign).

### Step 3 — Fetch note history

Pull the full note history for each linked record:

```bash
attio notes list --parent-object people --parent-record-id <record_id> --json
```

For deal-linked tasks, pull notes from both the deal and the associated people records.

Sort notes descending by `created_at`. Use up to the 5 most recent notes as context — this is enough to reconstruct the last meaningful interaction without blowing context.

**Summarize the note history into a 3-5 sentence contact context summary:**
- What was the last meaningful interaction?
- What was the stated next step?
- How long ago did contact go dark?
- Any signals worth referencing (objection raised, timing issue, budget concern)?

### Step 4 — Load LeadGrow voice + ICP context

Before generating any copy, load both files:

- `leadgrow-hq/company/voice-guide.md` — writing rules, tone, structure
- `leadgrow-hq/company/ICP.md` — who we're targeting and why

Key voice rules to enforce in every message:
- Short sentences. 8th grade reading level. No jargon.
- Specific over generic. Reference real context from their note history.
- No filler phrases ("just checking in", "hope you're well", "I wanted to circle back").
- Conversational, not corporate. Sound like Mitch wrote it himself.
- One clear ask per message. No multi-ask emails.
- No dashes of any kind (no em-dash, no double-hyphen). Use periods or parentheses instead.

### Step 5 — Generate follow-up message

Using the contact context summary, note history, voice guide, and ICP, write a personalized follow-up message for this specific contact.

**Message structure:**
1. **Opening line** — specific reference to the last interaction or something concrete about their situation. Never "just checking in."
2. **One sentence of value or relevance** — why now matters, or what's changed.
3. **Clear ask** — one thing. Reply, call, decision, intro. Nothing more.

**Target length:** 4-6 sentences. Shorter is better. Cold outbound rules apply even for warm follow-ups — respect their time.

**Personalization anchors to pull from note history (in priority order):**
1. Specific thing they said in a call or email
2. A problem or objection they named
3. A next step that was agreed to but not executed
4. Their company situation / deal stage
5. Time elapsed ("it's been six weeks since...")

### Step 6 — Present to Mitch (per-contact loop)

Present one contact at a time. Format:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVERDUE FOLLOW-UP — [N of TOTAL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTACT
  Name:     Jordan Lee
  Title:    VP Sales
  Company:  Boundless
  Email:    jordan@boundless.com
  Task:     Schedule intro call  (Overdue 7d)

CONTEXT
  Last interaction: Call on Mar 12. Jordan said timing was bad — Q1
  close crunch. Said to follow up mid-April. Budget confirmed at ~$5k/mo.
  No contact since the call. Task was created that day and never updated.

DRAFT FOLLOW-UP
──────────────────────────────────────────────────
Subject: Re: Boundless outbound — April timing

Jordan,

You mentioned Q1 close was the blocker and mid-April would work better.
We're there. I've got one spot opening up in the next engagement cycle
and wanted to give you first right of refusal before I fill it.

Worth 20 minutes this week?

— Mitch
──────────────────────────────────────────────────

Actions: [a] approve  [e] edit  [s] skip  [c] mark complete  [d] done for today
> _
```

Wait for Mitch's response before moving to the next contact.

---

## User Actions

### `a` — Approve

Accept the draft as-is.

**Always:**
```bash
# Push the task deadline by 7 days (default snooze on approved follow-up)
attio tasks update <task_id> --deadline <now+7d in ISO 8601>

# Add a note to the linked record logging that the follow-up was sent
attio notes create \
  --parent-object <target_object> \
  --parent-record-id <target_record_id> \
  --title "Follow-up sent — <today's date>" \
  --content "<approved message body>"
```

**If `--queue-approved` flag is set:**
Queue the message to EmailBison. Use `bison_mcp` tools to create a single-step campaign or add to an existing reply sequence for this contact. Print the campaign/draft link after queuing.

**If no `--queue-approved` flag:**
Print the approved message to screen in a clean copyable block. Mitch sends it manually.

Then advance to the next contact.

### `e` — Edit

Open the draft for inline editing. Claude prompts: `Edit the message (or describe what to change):`

If Mitch types a new message directly, use that verbatim.
If Mitch describes a change ("make it shorter", "reference the pricing doc they asked for"), Claude rewrites and re-presents the full draft for a second approval pass.

After approval on the edited version, execute the same approve flow above.

### `s` — Skip

Leave the task untouched. Log nothing to Attio. Advance to the next contact.

Print: `Skipped. Task remains overdue.`

### `c` — Mark complete

```bash
attio tasks update <task_id> --completed
```

Print: `Task marked complete. Moving on.`

Advance to the next contact. No message generated or sent.

### `d` — Done for today

Stop the loop immediately. Print a summary of what was processed:

```
Session complete.
  Approved: 3 messages
  Edited + approved: 1 message
  Skipped: 2
  Marked complete: 1
  Remaining in queue: 4 (run again to continue)
```

Exit cleanly.

---

## Output

By end of session:

1. **Updated tasks** — approved contacts have new deadlines pushed 7 days
2. **Notes logged** — approved messages are recorded against the linked record in Attio
3. **Messages queued or printed** — depending on `--queue-approved` flag
4. **Session summary** — printed to screen with counts

No files written to disk unless Mitch asks for a session log.

---

## Context Files to Load

Load both before generating any copy. Do not generate follow-up messages without them.

| File | Path | Purpose |
|------|------|---------|
| Voice guide | `leadgrow-hq/company/voice-guide.md` | Tone, structure, writing rules |
| ICP | `leadgrow-hq/company/ICP.md` | Target profile, pain points, disqualifiers |

---

## attio-cli Commands Used

| Command | Purpose |
|---------|---------|
| `attio tasks list --not-completed --json` | Fetch all incomplete tasks |
| `attio tasks list --not-completed --linked-object <slug> --json` | Filter by object type |
| `attio tasks list --not-completed --assignee <actor_id> --json` | Filter by assignee |
| `attio tasks update <task_id> --deadline <iso8601>` | Push task deadline (snooze) |
| `attio tasks update <task_id> --completed` | Mark task complete |
| `attio records get --object <slug> --record-id <id> --json` | Fetch contact/deal record |
| `attio notes list --parent-object <slug> --parent-record-id <id> --json` | Fetch note history |
| `attio notes create --parent-object <slug> --parent-record-id <id> --title <t> --content <c>` | Log sent message as a note |
| `attio workspace members --json` | Resolve actor IDs to names/emails |

**Client-side filtering note:** The Attio v2 tasks endpoint does not support `deadline_before` as a query parameter. Overdue filtering is always done in Python after fetching all incomplete tasks.

---

## Example Invocations

### Morning review — all overdue follow-ups

```
Run overdue follow-up skill
```

Claude pulls all overdue tasks, fetches context, generates copy, presents one at a time.

### Deals only, queue approved messages

```
Run overdue follow-up for deals, queue approved messages to EmailBison
```

Claude runs with `--object deals --queue-approved` behavior.

### Limit to 5 contacts (high-priority batch)

```
Show me the 5 most overdue follow-ups
```

Claude pulls all overdue, sorts oldest-first, works through the top 5.

### Specific person

```
Generate a follow-up for Jordan Lee in Attio
```

Claude fetches the specific contact record, finds linked overdue tasks, runs the single-contact version of the loop.

---

## Implementation Notes

1. **Deadline filtering is client-side.** Attio v2 does not expose `deadline_before` on the tasks endpoint. Fetch all incomplete tasks, filter in Python.

2. **Note history caching.** Cache note fetches by `(parent_object, parent_record_id)`. Deal tasks often share contacts; this avoids redundant calls.

3. **Deal-linked tasks need double resolution.** Fetch the deal record first, then extract associated person IDs (`associated_people` attribute) to get the right email and name for the message.

4. **No message is sent without explicit approval.** Claude generates copy; Mitch decides. This is non-negotiable. Never auto-approve or skip the action prompt.

5. **EmailBison queuing (--queue-approved).** Use `bison_mcp` tools. For a new prospect, create a 1-step campaign with the approved message. For an active deal or existing contact, add a step to their existing sequence. Check `leadgrow-hq/archive/mcp-docs/EmailBison.md` for the correct tool calls.

6. **Ctrl+C handling.** If Mitch exits mid-loop, print the session summary with what was processed before exit. Do not leave partial state.

7. **Object display order.** Always process `deals` first, then `people`, then `companies`. Deals are highest pipeline priority.
