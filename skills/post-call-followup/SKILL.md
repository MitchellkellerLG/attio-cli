---
name: post-call-followup
description: >
  Pulls a contact's Attio record + most recent call note via attio-cli, then
  generates a personalized follow-up email in LeadGrow voice grounded in what
  was actually discussed. Interactive review loop — show draft, wait for
  approval or edits, then create an Attio task ("send follow-up to [name]")
  with a 24h deadline and optionally push the draft to EmailBison.
  Trigger when Mitch says "write a follow-up for [name]", "post-call email
  for [contact]", "follow up on my call with [name]", or similar.
version: 0.1.0
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

## Inputs

Mitch provides one of:
- Contact name (e.g. "Sarah Chen")
- Contact email (e.g. "sarah@acme.com")
- Attio record ID (e.g. `rec_01abc123`)

If Mitch provides a name only and there are multiple matches, list them and ask him to confirm before proceeding.

---

## What Claude Does

### Step 1 — Pull contact record from Attio

Run the following to find the contact:

```bash
# By name
attio people search --query "Sarah Chen" --json

# By email
attio people search --email "sarah@acme.com" --json

# By record ID (skip search)
attio people get --id "rec_01abc123" --json
```

Extract from the response:
- Full name
- Company name and title
- Email address
- Any existing attributes (deal stage, tags, source)

If the contact is not found, tell Mitch and stop. Do not guess or proceed with partial data.

### Step 2 — Pull the most recent note (call summary)

```bash
attio notes list --record-id "<record_id>" --limit 5 --json
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
  --record-id "<record_id>" \
  --title "Send follow-up email to [First Name]" \
  --due-date "<24h from now, ISO 8601>" \
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

---

## attio-cli Commands Used

| Command | Purpose |
|---------|---------|
| `attio people search --query "..." --json` | Find contact by name |
| `attio people search --email "..." --json` | Find contact by email |
| `attio people get --id "..." --json` | Fetch full record by ID |
| `attio notes list --record-id "..." --limit 5 --json` | Pull recent notes |
| `attio tasks create --record-id "..." --title "..." --due-date "..." --json` | Create follow-up task |

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
2. attio notes list --record-id "rec_01xyz" --limit 5 --json
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
