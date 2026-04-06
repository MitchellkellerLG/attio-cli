---
title: Post-Call Processing
type: workflow
created: 2026-04-01
estimated-time: 10-15 minutes
tools:
  - attio-cli (notes create, tasks create)
  - post-call-followup skill
---

# Post-Call Processing

Log the call, generate the follow-up, create the next-action task — before the context fades. Run this within 1 hour of any sales or discovery call. The longer you wait, the more you lose.

This workflow has two phases: (1) log the raw call note to Attio immediately, (2) run the follow-up skill to generate the email and task. The note comes first because it's your source of truth. The skill pulls directly from it.

---

## Prerequisites

- `attio` CLI installed and authenticated
- The contact exists in Attio, or you have their email to create them
- Call notes ready (bullet points, voice memo transcript, or just 3-5 key takeaways)

---

## Step-by-Step

### Step 1 — Log the call note to Attio (3-5 min)

Do this first, even before generating the follow-up. The note is the source of truth.

**If the contact already exists in Attio, log by record ID:**

```bash
# First, find the contact
attio people search --query "Sarah Chen" --json
# or by email (more reliable)
attio people search --email "sarah@acme.com" --json
```

Extract `data[0].id.record_id` — this is `PERSON_ID`.

Then create the note:

```bash
attio notes create \
  --parent-object people \
  --parent-record-id "rec_01abc123" \
  --title "Discovery call — 2026-04-01" \
  --content "Pain: low reply rates, no ICP definition. Interested in Clay enrichment + sequencing. Q2 starts May 1 — timing good. Asked about pricing, will follow up. Next: send case study deck + pricing overview." \
  --json
```

**If the contact is new (not yet in Attio), assert them first:**

```bash
attio people assert \
  --matching-attribute email_addresses \
  --values '{"email_addresses": [{"email_address": "sarah@acme.com"}], "name": [{"full_name": "Sarah Chen"}]}' \
  --json
```

Extract the `record_id` from the response, then create the note using that ID as shown above.

**Note content guidelines:**

Keep it raw and factual. Don't polish. The follow-up skill will use this verbatim.

Include at minimum:
- Their stated pain (use their exact words where possible)
- What you pitched or discussed
- Any objections or timing issues they mentioned
- Agreed next steps
- Any creative ideas or specific angles that came up

**Example note content:**

```
Pain: Cold email volume is low and reply rates are 1-2%. No clear ICP — targeting anyone at "mid-market SaaS." Team can't explain why emails aren't converting.

Pitched: ICP definition + Clay enrichment for better signal targeting + EmailBison for sequencing. Showed example reply rate results from similar clients.

Objections: Budget tight in Q1. Q2 budget opens April. CFO approval needed for anything over $3k/mo.

Agreed next: I'll send a case study + pricing breakdown. They'll loop in their VP Sales for the next call. Follow up in 2 weeks.

Creative angle: Used the phrase "spray and pray" themselves — good hook for the follow-up.
```

Confirm the note was created. The CLI will return a `note_id`.

---

### Step 2 — Run post-call-followup skill (5-8 min)

Now that the note is in Attio, run the skill:

```
Write a follow-up for Sarah Chen from Acme.
```

The skill will:
1. Pull Sarah's Attio record
2. Pull the note you just created
3. Load the voice guide and ICP
4. Generate a personalized follow-up email
5. Show you the draft for review

**Interactive review loop:**

```
--- DRAFT FOLLOW-UP ---
Subject: Sarah - quick follow-up

[generated email body]
--- END DRAFT ---

Ready to send? Options: approve to create the Attio task + push to EmailBison,
edit to revise, or regenerate to start fresh.
```

- **approve** — creates a task "Send follow-up email to Sarah" due in 24h and saves/queues the draft
- **edit** — describe what to change, Claude revises, shows again
- **regenerate** — start fresh with a different angle

---

### Step 3 — Confirm Attio task was created (30 sec)

After approval, the skill creates a task automatically:

```bash
# What the skill runs internally:
attio tasks create \
  --record-id "rec_01abc123" \
  --title "Send follow-up email to Sarah" \
  --due-date "2026-04-02T09:00:00.000Z" \
  --json
```

The skill will print the task ID and due date. Confirm you see it before closing the session.

---

### Step 4 — Optional: Push draft to EmailBison

After approval, the skill asks:

```
Push draft to EmailBison as a manual send draft? (yes/no)
```

- **yes** — draft is created in EmailBison with status "draft", not scheduled or sent
- **no** — draft is saved to `C:/Users/mitch/Everything_CC/temp/scratch/followup-sarah-chen-2026-04-01.md`

If you choose "no", you'll manually copy-paste from the temp file when you're ready to send.

---

## Handling Multiple Contacts on the Call

If two or more prospects were on the call (e.g., a VP and their director), run the workflow once for each person.

1. Log the note to the primary contact's record (the decision-maker)
2. Also log a shorter note to any secondary contacts: "Discovery call with [Name] + [Primary Contact]. See [Primary]'s record for full notes."
3. Run the follow-up skill separately for each person who needs a follow-up

If only one person needs a direct follow-up (e.g., the others were just observers), you only need to run Steps 2-4 for that person.

---

## If You Can't Run It Immediately

Sometimes you're back-to-back and can't process the call in the moment. Here's how to handle it:

**Within the next hour (before the call fades):**

1. Open a notes app or `temp/scratch/` and dump raw notes immediately after the call
2. Even 5 bullet points is enough — capture the key pain, objections, and next steps

**When you have 15 minutes:**

1. Log the note to Attio using the Step 1 commands (your raw notes become the `--content`)
2. Run the skill — it'll pick up the note you logged

**If you saved raw notes to temp/ first:**

```bash
# Your temp note file: temp/scratch/call-notes-sarah-chen-2026-04-01.txt
# Copy its content into the notes create command:

attio notes create \
  --parent-object people \
  --parent-record-id "rec_01abc123" \
  --title "Discovery call — 2026-04-01" \
  --content "$(cat 'C:/Users/mitch/Everything_CC/temp/scratch/call-notes-sarah-chen-2026-04-01.txt')" \
  --json
```

Then run the skill as normal.

**Absolute deadline:** Log the call note before the end of the day. After 24 hours, the follow-up loses specificity and the contact starts to feel like cold outreach again.

---

## Batch Processing (Multiple Calls Same Day)

If you had 3+ calls today, use bulk mode instead of running the workflow per contact:

```
Write follow-ups for all my calls today.
```

The skill scans for all notes created in the last 24 hours with titles containing "call", "meeting", "discovery", or "sync". Builds a queue. Processes each one in the same interactive loop.

**Or use export mode to review before sending:**

```
Write follow-ups for all my calls today — export to file.
```

Generates all drafts to `temp/scratch/followups-2026-04-01.md`. Review at your own pace. Send manually from there.

---

## Done Criteria

The post-call workflow is complete when:

1. A call note exists in Attio on the contact's record (check: `attio notes list --record-id <id> --limit 1 --json`)
2. A follow-up email draft is approved (either queued to EmailBison or saved to temp/)
3. A task "Send follow-up email to [Name]" exists in Attio with a deadline within 24 hours

If the task doesn't exist, the follow-up will never get sent. The task is the commitment.

---

## Common Errors

**"Contact not found in Attio"**
The person may be under a slightly different name. Try searching by email instead:
```bash
attio people search --email "sarah@acme.com" --json
```
If they genuinely don't exist, use `attio people assert` to create them (see Step 1).

**"Most recent note doesn't appear to be a call summary"**
The skill will flag this if the note title doesn't contain "call", "meeting", "discovery", or "sync". It'll ask you to confirm before proceeding. If it's correct, confirm and proceed. Use a consistent title format (e.g., "Discovery call — YYYY-MM-DD") to avoid this.

**`notes create` fails with a 400 error**
Most common cause: special characters or unescaped quotes in the `--content` value. If your note content contains single quotes, either escape them (`\'`) or use a temp file approach:

```bash
# Write content to a temp file first
echo "Call note content here" > /tmp/note-content.txt
attio notes create \
  --parent-object people \
  --parent-record-id "rec_01abc123" \
  --title "Discovery call — 2026-04-01" \
  --content "$(cat /tmp/note-content.txt)" \
  --json
```

**Multiple contacts match the name**
The skill will list all matches (name, company, email) and ask you to pick one. Provide the index number or the record ID to proceed.

**`tasks create` fails after note succeeds**
Note is already logged — don't re-run the whole workflow. Create the task manually:

```bash
attio tasks create \
  --record-id "rec_01abc123" \
  --title "Send follow-up email to Sarah Chen" \
  --due-date "2026-04-02T09:00:00.000Z" \
  --json
```
