---
name: post-call-followup
description: >
  Pulls a contact's Attio record + most recent call note via attio-cli, then
  generates a personalized follow-up email in LeadGrow voice grounded in what
  was actually discussed. Interactive review loop — show draft, wait for
  approval or edits, then create an Attio task ("send follow-up to [name]")
  with a 24h deadline and optionally push the draft to EmailBison.
  Supports single contact mode and --bulk mode to batch all call notes from
  the last N hours into a review loop.
  Trigger when Mitch says "write a follow-up for [name]", "post-call email
  for [contact]", "follow up on my call with [name]", "write follow-ups for
  all my calls today", or similar.
version: 0.2.0
triggers:
  - write a follow-up for
  - post-call email
  - follow up on my call with
  - follow-up email for
  - send a follow-up to
  - after the call with
  - recap email for
  - follow up with [name] from the call
  - draft follow-up
  - attio follow-up
  - write follow-ups for all my calls
  - batch follow-ups
  - follow-ups from today
  - all my calls today
  - post-call batch
---

# Post-Call Follow-Up

Pull contact context from Attio, generate a personalized follow-up email in LeadGrow voice, get Mitch's sign-off, then create the task and optionally push to EmailBison.

---

## When to Use

Use when Mitch has just finished a sales or discovery call and needs a follow-up email drafted based on what was discussed.

**Trigger conditions:**
- Mitch references a person by name after a call ("write a follow-up for Sarah")
- Mitch says "follow up on my call with X"
- Mitch asks for a post-call email, recap, or next-steps email

**Do not use for:**
- Outbound cold emails (use `campaign-copywriting` skill)
- Follow-ups with no prior call context in Attio notes
- Checking in on prospects without a recent call note

---

## Modes

### Single-contact mode (default)

Mitch provides one of:
- Contact name (e.g. "Sarah Chen")
- Contact email (e.g. "sarah@acme.com")
- Attio record ID (e.g. `rec_01abc123`)

If Mitch provides a name only and there are multiple matches, list them and ask him to confirm before proceeding.

### Bulk mode (`--bulk`)

Triggered when Mitch says "write follow-ups for all my calls today", "batch follow-ups", or uses the `--bulk` flag.

Scans all Attio notes created in the last N hours (default: 24) where the note title contains "call", "meeting", "discovery", or "sync". Groups by contact. Deduplicates — one follow-up per contact max. Queues all matching contacts into an interactive review loop identical to `overdue-follow-up` (one at a time, same action keys).

**Bulk flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--bulk` | flag | off | Enable batch mode. Scans notes for call summaries instead of requiring a contact name. |
| `--since-hours <n>` | int | `24` | Look back N hours for call notes. Use `48` after a day off, `72` after a long weekend. |
| `--limit <n>` | int | none | Cap the queue to N contacts. Oldest call notes first. |
| `--export` | flag | off | Skip interactive review. Generate all drafts, write to `temp/scratch/followups-YYYY-MM-DD.md`. Nothing sends. Use for review-later or morning prep. |

## Inputs

---

## What Claude Does

### Step 0 (bulk mode only) — Discover call notes

If `--bulk` is active, scan notes workspace-wide before doing anything else:

```bash
# Pull all notes created in the last N hours
attio notes list --json --limit 200
```

Filter client-side:
- `note.created_at >= now() - since_hours`
- `note.title` contains any of: "call", "meeting", "discovery", "sync", "intro" (case-insensitive)

Group by `note.parent_record_id`. If multiple call notes exist for the same contact, use the most recent. Build the queue in ascending `created_at` order (oldest calls get follow-ups first).

Print the queue before starting the review loop:

```
Found 5 contacts with call notes in the last 24 hours:
  1. Sarah Chen (Acme) — Discovery call (3h ago)
  2. Jordan Lee (Boundless) — Intro call (6h ago)
  3. Marcus Webb (Storylane) — Proposal review call (8h ago)
  4. Priya Nair (Tensorlake) — Follow-up call (14h ago)
  5. Chris Torres (Teachaid) — Discovery call (22h ago)

Processing each one. [Ctrl+C to stop early]
```

Then proceed to Step 1 for each contact in the queue.

### Step 1 — Pull contact record from Attio

Run the following to find the contact:

```bash
# By name
attio people search --query "Sarah Chen" --json

# By email
attio people search "sarah@acme.com" --json

# By record ID (skip search)
attio people get rec_01abc123 --json
```

Extract from the response:
- Full name
- Company name and title
- Email address
- Any existing attributes (deal stage, tags, source)

If the contact is not found, tell Mitch and stop. Do not guess or proceed with partial data.

### Step 2 — Pull the most recent note (call summary)

```bash
attio notes list --parent-object people --parent-record-id "<record_id>" --json
```

Take the most recent note. If the note has a title containing "call", "meeting", or "discovery" — that's the one. If none match, take the most recent note and flag it to Mitch: "Most recent note doesn't appear to be a call summary — using it anyway. Confirm?"

Extract from the note:
- Key pain points discussed (exact phrases where possible)
- What Mitch offered or pitched
- Any objections or concerns raised
- Agreed next steps from the call
- Creative angles or unique ideas Mitch floated

### Step 3 — Load context

Read both files before writing:

1. `C:/Users/mitch/Everything_CC/leadgrow-hq/company/voice-guide.md` — Mitchell's writing voice
2. `C:/Users/mitch/Everything_CC/leadgrow-hq/company/ICP.md` — ICP context for framing

### Step 4 — Generate the follow-up email

Write the email using these rules:

**Structure:**
1. Subject line: `[First name] - quick follow-up`
2. Opening: One sentence acknowledging the call. Warm, not corporate.
3. Pain recap: 2-4 bullet points using their exact language from the note. Not translated. Not polished.
4. How LeadGrow helps: 2-3 specific bullets tied directly to their situation. No generic agency speak.
5. Creative angle (if one was discussed on the call): Their exact words or Mitch's verbatim framing. Do not polish.
6. CTA: One clear, low-friction next step. Either confirm next meeting, share a resource, or ask one specific question.
7. Sign-off: "- Mitchell" or "- Mitch" depending on how the note reads.

**Voice rules (non-negotiable):**
- No em dashes. No double hyphens. Use periods or commas.
- Short sentences. 8th grade reading level.
- Use their exact phrases for pain points. Do not translate to marketing speak.
- Specific over generic. Real numbers, real situations, real context from the call.
- No superlatives. No "world-class", "best", "revolutionary".
- Confident but proof-driven. "We typically see X" not "we're the best at X".
- No filler openers. Not "I hope this email finds you well." Just get into it.

---

## Interactive Review

After generating the draft, display it in full inside a clearly labeled block:

```
--- DRAFT FOLLOW-UP ---
Subject: [subject]

[body]
--- END DRAFT ---
```

Then ask:

> "Ready to send? Options: **approve** to create the Attio task + push to EmailBison, **edit** to revise (tell me what to change), or **regenerate** to start fresh."

**Approve:** Proceed to Step 5.

**Edit:** Mitch describes what to change. Rewrite only the affected sections. Re-display the full updated draft. Ask again.

**Regenerate:** Ask what wasn't working (tone, angle, structure). Start Step 4 again with that context.

Do not proceed to Step 5 without explicit approval.

---

## Output

### Always: Create Attio task

Once approved, create a follow-up task in Attio on the contact's record:

```bash
attio tasks create \
  --content "Send follow-up email to [First Name]" \
  --deadline "<24h from now, ISO 8601>" \
  --linked-record '{"target_object":"people","target_record_id":"<record_id>"}' \
  --json
```

Confirm task creation with the task ID and due date.

### Optional: Push to EmailBison

Ask: "Push draft to EmailBison as a manual send draft? (yes/no)"

If yes, use the EmailBison MCP to create a draft campaign. Set status to draft. Do not schedule or activate.

If no, save the approved draft to:
```
C:/Users/mitch/Everything_CC/temp/scratch/followup-[contact-name]-[YYYY-MM-DD].md
```

### Bulk export mode (`--export`)

When `--export` is set, skip all interactive review. Generate all drafts and write them to:

```
C:/Users/mitch/Everything_CC/temp/scratch/followups-[YYYY-MM-DD].md
```

File format:

```markdown
# Post-Call Follow-Ups — 2026-04-01
Generated: 5 drafts

---

## 1. Sarah Chen — Acme Corp

**Subject:** Sarah - quick follow-up
**Contact:** sarah@acme.com
**Call note:** Discovery call (3h ago)

[email body]

---

## 2. Jordan Lee — Boundless
...
```

Print the file path and draft count when done. Nothing is sent, no Attio tasks are created. Mitch reviews the file and decides what to send manually.

---

## attio-cli Commands Used

| Command | Purpose |
|---------|---------|
| `attio people search --query "..." --json` | Find contact by name |
| `attio people search "..." --json` | Find contact by email |
| `attio people get <record_id> --json` | Fetch full record by ID |
| `attio notes list --parent-object people --parent-record-id "..." --json` | Pull recent notes |
| `attio tasks create --content "..." --deadline "..." --linked-record '{"target_object":"people","target_record_id":"..."}' --json` | Create follow-up task |

---

## Context Files to Load

| File | Purpose |
|------|---------|
| `C:/Users/mitch/Everything_CC/leadgrow-hq/company/voice-guide.md` | Mitchell's writing voice — load before drafting |
| `C:/Users/mitch/Everything_CC/leadgrow-hq/company/ICP.md` | ICP signals for framing the offer |

---

## Example Invocation

```
Mitch: "Write a follow-up for Sarah Chen from Acme."

Claude:
1. attio people search --query "Sarah Chen" --json
2. attio notes list --parent-object people --parent-record-id "rec_01xyz" --json
3. Loads voice-guide.md + ICP.md
4. Generates draft
5. Displays draft for review
6. On approval: attio tasks create + saves draft or pushes to Bison
```

---

## Failure States

| Situation | Action |
|-----------|--------|
| Contact not found in Attio | Tell Mitch. Stop. Do not guess. |
| No notes on the contact | Tell Mitch. Ask if he wants to proceed with just the record fields or paste call notes manually. |
| Most recent note is not a call summary | Flag it. Show the note title + date. Ask Mitch to confirm before using. |
| Multiple contacts match the name | List all matches (name, company, email). Ask Mitch to pick one. |
| attio-cli command fails | Show the error. Do not retry blind. Check `attio --help` or ask Mitch for the correct flag. |
