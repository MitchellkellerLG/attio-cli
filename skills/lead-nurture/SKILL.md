---
name: lead-nurture
description: >
  Interactive nurture workflow for stale pipeline contacts. Pulls contacts from an Attio
  list or stage (e.g. "Nurture", "Interested - No Response"), filters to those with no
  activity in the last N days, loads LeadGrow voice + ICP context, and generates a
  tailored follow-up message per contact based on their history, role, company, and last
  touchpoint. Presents contacts one at a time for Mitch to approve, edit, or skip. On
  approve: queues message to EmailBison and creates a follow-up task in Attio.
  Supports --bulk-approve (approve all without per-contact review), --export (generate
  all drafts to file, nothing sends), and --multi-list (run across multiple lists in
  one session). Use this when pipeline is going cold, before weekly reviews, or when
  a list has 5+ contacts with no recent touch.
version: 0.2.0
triggers:
  - nurture contacts
  - follow up with stale leads
  - who needs a touch
  - pipeline going cold
  - no response follow-up
  - nurture list
  - interested no response
  - reactivate leads
  - warm up cold contacts
  - weekly nurture run
  - draft nurture messages
---

# Skill: `lead-nurture`

**Project:** attio-cli
**Layer:** Workflow skill (multi-command orchestration + interactive review)
**Audience:** Claude Code executing this skill with Mitch in the loop for every approval

---

## When to Use

Run this skill when:

- A pipeline list (e.g. "Nurture", "Interested - No Response", "Proposal Sent") has gone quiet
- It's been 7+ days since any activity on a batch of contacts
- Mitch asks who needs a touch, a follow-up, or a reactivation message
- Weekly pipeline hygiene — reviewing who's gone cold before new outreach starts

This is **interactive by design.** Nothing sends without Mitch approving it. Claude generates; Mitch decides.

---

## Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| List name or ID | string | required (unless `--multi-list`) | Attio list name (e.g. `"Nurture"`) or list ID. Case-insensitive name match is fine. |
| `--days <n>` | int | `7` | Filter to contacts with no notes or tasks updated in the last N days. |
| `--persona <filter>` | string | none | Optional. Filter by job title keyword (e.g. `"VP Sales"`, `"Head of Growth"`). Applied client-side against contact title field. |
| `--limit <n>` | int | none | Cap the review queue to N contacts. Useful for large lists — process in batches. |
| `--bulk-approve` | flag | off | Skip per-contact review. Generate all drafts, show summary table, confirm once to approve all. |
| `--export` | flag | off | Dry-run mode. Generate all drafts, write to `temp/scratch/nurture-[list]-YYYY-MM-DD.md`. Nothing sends. |
| `--multi-list <list1,list2,...>` | string | none | Run across multiple lists in one session. Each list processes sequentially. Separate list names with commas. |

---

## What Claude Does

### Step 1 — Resolve the list

Find the list by name:

```bash
attio lists list --json
```

Match the list name case-insensitively. If no match, surface available list names and halt.

Once matched, capture the `list_id`.

### Step 2 — Pull all entries on the list

```bash
attio lists entries list <list_id> --json
```

This returns list entries with linked record IDs. Each entry links to a `people` or `companies` record. Capture all `record_id` values and their linked object type.

### Step 3 — Fetch full contact records + notes

For each record on the list:

```bash
attio records get --object people --record-id <record_id> --json
attio notes list --parent-object people --parent-record-id <record_id> --json
attio tasks list --linked-object people --linked-record-id <record_id> --not-completed --json
```

Cache all fetches in-memory. Do not re-fetch the same record twice if it appears on multiple lists.

### Step 4 — Filter by inactivity (client-side)

The Attio API does not expose a last-activity filter. Apply client-side:

1. Find the most recent timestamp across:
   - `note.created_at` for all notes on the record
   - `task.updated_at` for all tasks linked to the record
   - `list_entry.updated_at` from the list entry itself
2. Keep only records where `max(all timestamps) < now() - N days`

```python
from datetime import datetime, timezone, timedelta

cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)

def last_activity(record_id: str) -> datetime | None:
    timestamps = []
    for note in notes_by_record.get(record_id, []):
        if note.get("created_at"):
            timestamps.append(datetime.fromisoformat(note["created_at"].replace("Z", "+00:00")))
    for task in tasks_by_record.get(record_id, []):
        if task.get("updated_at"):
            timestamps.append(datetime.fromisoformat(task["updated_at"].replace("Z", "+00:00")))
    return max(timestamps) if timestamps else None

stale = [r for r in records if (last_activity(r["id"]) or datetime.min.replace(tzinfo=timezone.utc)) < cutoff]
```

Records with **no notes or tasks at all** are always included — they've never been touched.

### Step 5 — Apply optional persona filter

If `--persona` was passed, filter `stale` records client-side:

```python
keyword = persona_filter.lower()
stale = [r for r in stale if keyword in (r.get("job_title") or "").lower()]
```

### Step 6 — Apply limit

If `--limit` was passed, truncate the filtered list to N contacts. Sort by last activity ascending (oldest-touched first) before truncating — worst-neglected contacts get prioritized.

### Step 7 — Load voice + ICP context

Before generating any messages, load:

```
leadgrow-hq/company/voice-guide.md
leadgrow-hq/company/ICP.md
```

Hold both in context for the full message generation loop. Do not regenerate from scratch for each contact — apply the voice guide as a standing constraint.

### Step 8 — Generate nurture messages

For each contact in the queue, generate a tailored follow-up. Use all available context:

- Contact name, title, company
- Company description (from record attributes)
- The full note history — what was discussed, what they said, what was promised
- The list they're on (signals their stage: "Interested" = different message than "Nurture")
- Days since last activity
- Any open tasks (signals what was pending)

**Message generation rules:**

- 3–5 sentences max. No fluff. No "just checking in."
- Opens with a specific reference to the last conversation or something relevant to their situation
- Has one clear ask or one piece of value (a result, a quick question, a relevant observation)
- Sounds like Mitch: matter-of-fact conviction, no filler phrases, no em-dashes
- Subject line: 4 words or fewer, no punctuation, no caps except proper nouns
- If there are zero notes on the contact, generate a light cold-touch message based on their role + company only. Flag it as "[No history — first touch]" in the review display.

---

## Filtering Logic

**Included in queue:**
- On the target list
- Last activity > N days ago (or no activity ever)
- Matches persona filter if provided
- `is_completed` is false on any open tasks (contact still active in pipeline)

**Excluded from queue:**
- Activity within the last N days
- List entry `stage` = "Closed Won" or "Closed Lost" (if stage tracking is on the list)
- Contact record has `do_not_contact` attribute set to true

**Edge cases:**
- If a contact has notes but all are older than 90 days, flag them as `[Long-stale — verify still relevant]` in the review header
- If the last note was a reply from the contact (detected by note title prefix `"Reply:"` or similar), flag as `[Replied — review before messaging]` and still include in queue — Mitch decides

---

## Per-Contact Review Loop

Present one contact at a time. Format:

```
────────────────────────────────────────────────
CONTACT 1 OF 7 — Nurture list
────────────────────────────────────────────────
NAME:      Jordan Lee
TITLE:     VP of Sales
COMPANY:   Acme Corp
LAST TOUCH: 14 days ago (2026-03-17)
STAGE:     Interested - No Response

HISTORY SUMMARY:
  • 2026-03-10: Intro call. Expressed interest in cold email for SMB segment.
                Asked about EmailBison pricing. Said to follow up in 2 weeks.
  • 2026-03-17: Sent pricing deck. No reply.

OPEN TASKS:
  • Follow up after pricing deck (due 2026-03-24, overdue)

────────────────────────────────────────────────
DRAFT MESSAGE:

Subject: pricing question

Jordan — wanted to check if you had a chance to look through the deck.
Most teams in your space are running 3–4 sequences by month two. Happy
to walk through what that looks like for Acme specifically if it'd help
move things forward.

Worth a quick call this week?

— Mitch
────────────────────────────────────────────────
[a] Approve and queue
[e] Edit message
[s] Skip (keep on list)
[r] Remove from list
[q] Quit (save progress)
>
```

**Approve [a]:** Queue to EmailBison + create Attio task. Move to next contact.

**Edit [e]:** Open draft in an editable prompt. Mitch types the revised message. On save, show the edited version and re-prompt for `[a]` to confirm or `[s]` to skip.

**Skip [s]:** Leave contact on list unchanged. Log the skip with timestamp. Move to next contact.

**Remove [r]:** Prompt "Remove Jordan Lee from [list name]? (y/n)". On confirm, call remove command. Move to next contact.

**Bulk approve [b]:** Approve all remaining contacts in the queue without individual review.

Print a confirmation:

```
Bulk approve remaining 4 contacts?
  • Marcus Webb (Boundless) — 9d stale
  • Priya Nair (Tensorlake) — 14d stale
  • Alex Kim (Aurium) — 18d stale  ⚠️ Long-stale
  • Sam Park (Teachaid) — 8d stale

⚠️ = flagged contacts. Recommended: review these individually.

Approve all 4? [y] yes  [e] exclude flagged  [n] return to loop
> _
```

On `y`: Execute approve flow for all remaining. On `e`: Approve non-flagged, queue flagged for individual review. On `n`: Return to loop.

**Quit [q]:** Exit the loop. Print session summary. All approved messages already queued remain in the queue — no rollback.

---

## User Actions

### Approve — queue to EmailBison

This does **not** create a full campaign. It queues a one-off message to a single contact.

Steps:
1. Resolve the contact's primary email from Attio record attributes
2. Add as a new contact to the appropriate EmailBison campaign (or create a single-contact sequence if no nurture campaign exists)
3. Create a follow-up task in Attio

```bash
# Get contact email
attio records get --object people --record-id <record_id> --json \
  | jq -r '.data.values.email_addresses[0].email_address'
```

EmailBison queue is handled via MCP (`bison_mcp`). Log the queued contact ID for the session summary.

### Create follow-up task in Attio

After queueing, immediately create a task:

```bash
attio tasks create \
  --linked-object people \
  --linked-record-id <record_id> \
  --content "Nurture message sent — follow up if no reply in 5 days" \
  --deadline <today+5d in ISO8601>
```

### Remove from list

```bash
attio lists entries delete <list_id> <entry_id>
```

Entry ID is captured from the original `attio lists entries list` response.

---

## Output

At session end, print a summary:

```
────────────────────────────────────────────────
NURTURE SESSION COMPLETE — 2026-03-31
────────────────────────────────────────────────
List:     Nurture
Reviewed: 7 contacts
Approved: 4 (messages queued to EmailBison, tasks created in Attio)
Skipped:  2
Removed:  1
────────────────────────────────────────────────
QUEUED:
  • Jordan Lee (Acme Corp) — follow-up task due 2026-04-05
  • Sarah Kim (Tensorlake) — follow-up task due 2026-04-05
  • Marcus Webb (Boundless) — follow-up task due 2026-04-05
  • Priya Nair (Storylane) — follow-up task due 2026-04-05
────────────────────────────────────────────────
```

---

## Context Files to Load

Load before entering the message generation loop. Hold for the full session.

| File | Purpose |
|------|---------|
| `leadgrow-hq/company/voice-guide.md` | LeadGrow brand voice — apply to every generated message |
| `leadgrow-hq/company/ICP.md` | Ideal customer profile — informs relevance of each nurture angle |

Do not re-read these files per contact. Load once, apply throughout.

---

## attio-cli Commands Used

| Command | Purpose |
|---------|---------|
| `attio lists list --json` | Resolve list name to list ID |
| `attio lists entries list <list_id> --json` | Pull all entries on the target list |
| `attio records get --object <obj> --record-id <id> --json` | Fetch full contact record + attributes |
| `attio notes list --parent-object <obj> --parent-record-id <id> --json` | Pull note history per contact |
| `attio tasks list --linked-object <obj> --linked-record-id <id> --not-completed --json` | Pull open tasks per contact |
| `attio tasks create --linked-object <obj> --linked-record-id <id> --content <text> --deadline <iso8601>` | Create follow-up task after approval |
| `attio lists entries delete <list_id> <entry_id>` | Remove a contact from the list |

EmailBison queueing is handled via `bison_mcp` MCP tools — not attio-cli directly.

---

## Bulk Approve Mode (`--bulk-approve`)

When `--bulk-approve` is set, skip the per-contact loop.

**Phase 1:** Pull all qualifying contacts, generate all drafts. Show progress: `Generating drafts... (4/9)`.

**Phase 2:** Show summary table:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NURTURE LIST — 9 drafts ready
List: Interested - No Response  |  Threshold: 7d
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   Contact               Stale    Flag      Opening line
  ─   ─────────────────     ──────   ──────    ──────────────────────────────
  1   Sarah Chen (Acme)     9d                 You asked about EmailBison pricing...
  2   Jordan Lee (Bdls)     14d                The deck we discussed — did you get a chance...
  3   Marcus Webb (Story)   7d                 Following up on the sequence we built...
  4   Priya Nair (Tensor)   22d      ⚠️ stale   It's been three weeks. One last note before...
  5   Chris Torres (Tch)    8d       📩 replied  You replied March 12 — looping back in...
...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ stale = 21+ days. 📩 replied = contact previously replied. Both warrant individual review.

Approve all 9? [y] yes  [r] review each  [e] exclude flagged, approve rest
> _
```

**Phase 3 — Execute on confirmation.**

---

## Export Mode (`--export`)

Generate all drafts and write to:

```
C:/Users/mitch/Everything_CC/temp/scratch/nurture-[list-name]-YYYY-MM-DD.md
```

File format:

```markdown
# Nurture Drafts — Interested - No Response — 2026-04-01
Generated: 9 drafts | Threshold: 7 days | List: Interested - No Response

---

## 1. Sarah Chen — Acme Corp
**Stale:** 9 days  **Stage:** Interested - No Response
**Email:** sarah@acme.com
**Last touch:** 2026-03-23 (sent pricing deck)

Subject: pricing question

Sarah — wanted to check if you had a chance to look through the deck.
Most teams in your space are running 3-4 sequences by month two.
Happy to walk through what that looks like for Acme specifically.

Worth a quick call this week?

— Mitch

---
```

Print file path and count. Nothing sends. No Attio writes.

---

## Multi-List Mode (`--multi-list`)

Run the nurture workflow across multiple lists in one session.

```
attio workflow lead-nurture --multi-list "Nurture,Interested - No Response,Proposal Sent" --days 7
```

Claude processes each list sequentially: resolves, filters, generates, reviews. At the end of each list, prints a mini-summary before moving to the next.

At session end, prints a combined summary:

```
MULTI-LIST NURTURE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nurture:                 4 approved, 1 skipped
Interested - No Response: 3 approved, 2 skipped
Proposal Sent:           2 approved, 1 removed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 9 messages queued, 7 tasks created
```

`--bulk-approve` and `--export` flags apply to each list when combined with `--multi-list`.

---

## Error Handling

### List not found

```
Error: No list matching "Nurture" found.
Available lists: Interested, Proposal Sent, Interested - No Response, Closed Won
```

Halt. Let Mitch correct the list name.

### Contact has no email address

Flag in review header: `[No email on record — cannot queue to EmailBison]`
Still show draft. Allow edit/skip/remove. On approve, warn: "No email found — message not queued. Add email to Attio record and re-run."

### API auth failure

```
Error: ATTIO_API_KEY not set or invalid. Run `attio config set api-key <key>` to configure.
```

Halt immediately.

### Rate limiting (429)

Handled by attio-cli's tenacity retry layer. No additional logic needed in this skill. If retries exhaust, surface the error and exit with a partial summary of what was completed before failure.

### Zero contacts after filtering

```
No contacts on "Nurture" list meet the criteria:
  — Days threshold: 7
  — Persona filter: none
  — Total on list: 12
  — Active in last 7 days: 12

All contacts have been touched recently. Nothing to nurture.
```

Exit cleanly.

---

## Example Invocation

```bash
# Full nurture run — all stale contacts on the Nurture list (default: 7 days)
attio workflow lead-nurture --list "Nurture"

# Tighten threshold — only contacts with no touch in 14+ days
attio workflow lead-nurture --list "Interested - No Response" --days 14

# VP-level only, cap at 5 contacts per session
attio workflow lead-nurture --list "Nurture" --persona "VP" --limit 5

# Proposal follow-ups that have gone quiet
attio workflow lead-nurture --list "Proposal Sent" --days 5
```

---

## Implementation Notes for Developer

1. **Inactivity filtering is entirely client-side.** The Attio v2 API has no `last_activity_before` parameter on list entries or records. Fetch all records, then filter in Python.

2. **Note history is the primary signal for message generation.** Always pull notes before generating. A contact with no notes gets a first-touch-style message; a contact with 3 detailed notes gets a highly specific reference. The quality difference is significant.

3. **Approve queues to EmailBison via MCP, not attio-cli.** The `bison_mcp` MCP server handles campaign/contact management. The skill calls MCP tools directly; do not attempt to build an EmailBison CLI wrapper inline.

4. **Session state should be tracked in-memory.** Keep a running list of approved, skipped, and removed contacts so the session summary is accurate even if the user quits mid-loop.

5. **Ctrl+C should exit gracefully.** Catch `KeyboardInterrupt` in the review loop. Print the session summary for however many contacts were processed before exit. Already-queued messages are not rolled back.

6. **Email resolution.** Attio stores emails under `values.email_addresses[]`. Take the first entry with `is_primary: true`, or fall back to the first entry in the array. If the array is empty, flag the contact as un-queueable.

7. **Date math for task deadlines.** Default follow-up task deadline = today + 5 business days. Compute in Python using `datetime` + manual weekday skipping (no third-party calendar library needed for this).

8. **Voice guide must be applied as a constraint, not a style suggestion.** Every draft goes through the voice rules before display. If a draft has em-dashes, filler phrases ("just wanted to"), or hedging language ("I thought maybe"), rewrite it before showing Mitch. He shouldn't have to catch voice violations in review.
