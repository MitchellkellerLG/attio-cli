---
name: deal-next-step
description: >
  Pull the full context on any Attio deal — stage, linked contacts, notes, open tasks — then
  diagnose where it's stuck and recommend the exact next action with a drafted message or
  talking points. Interactive review loop: Mitch approves, edits, or redirects before anything
  writes back to Attio. Use during weekly pipeline review, before calls, or when a deal has
  gone quiet. Triggers: deal review, pipeline review, next step, deal stuck, what should I do
  with this deal, follow up on deal, pre-call prep.
version: 0.1.0
maturity: draft
triggers:
  - deal review
  - pipeline review
  - deal next step
  - what should I do with this deal
  - deal is stuck
  - follow up on deal
  - pre-call prep
  - deal diagnosis
  - review my deals
  - prep for sales call
  - what's next with
  - advance deal
---

# Skill: deal-next-step

Pull the full deal context, diagnose the situation, recommend the next move, draft the outreach. Mitch reviews before anything writes back to Attio.

---

## When to Use

- **Weekly pipeline review** — run through every active deal, confirm next actions are real
- **Stuck deals** — deal has been in the same stage too long, last activity was weeks ago
- **Pre-call prep** — pull everything said so far, generate talking points for the next meeting
- **After a new note or reply lands** — re-evaluate what the deal needs now

---

## Inputs

One of the following is required. Everything else is pulled from Attio.

| Input | Type | Notes |
|-------|------|-------|
| `deal_identifier` | string | Deal name, linked contact email, or Attio deal record ID. The most specific identifier you have. |
| `--all-active` | flag | Skip identifier. Run the skill across all deals not in Won or Lost. Used for full pipeline review sessions. |

---

## What Claude Does

### Step 1 — Resolve the deal record

If a deal record ID is provided directly, skip search.

If a name is provided:

```bash
attio deals search "<deal_name>" --json --limit 5
```

If a contact email is provided, find the person first, then pull their linked deals:

```bash
attio people search "<email>" --json --limit 3
# Get PERSON_ID from response, then:
attio records list deals --filter '{"linked_record": {"target_object": "people", "target_record_id": "<PERSON_ID>"}}' --json
```

If multiple deals match, list them and ask Mitch to confirm which one before proceeding.

Extract `data.id.record_id` — this is `DEAL_ID`.

---

### Step 2 — Pull the full deal record

```bash
attio records get deals <DEAL_ID> --json
```

Extract and store:

- `deal_name` — the deal's display name
- `stage` — current pipeline stage (e.g., "Discovery", "Proposal Sent", "Negotiation")
- `stage_entered_at` — when the deal entered the current stage (ISO 8601)
- `value` — deal value if set
- `linked_contacts` — array of linked person record IDs
- `linked_company` — linked company record ID if set

---

### Step 3 — Pull linked contact details

For each person in `linked_contacts` (usually one, occasionally two):

```bash
attio records get people <PERSON_ID> --json
```

Extract: name, email, job title, company name.

If a company is linked to the deal:

```bash
attio records get companies <COMPANY_ID> --json
```

Extract: company name, domain, industry if available.

---

### Step 4 — Pull all notes on the deal

```bash
attio notes list --parent-object deals --parent-record-id <DEAL_ID> --json
```

Sort notes by `created_at` descending (most recent first). Read the full content of each note. Notes contain call summaries, email history, context from previous interactions.

Also pull notes on the linked person record to catch context logged there:

```bash
attio notes list --parent-object people --parent-record-id <PERSON_ID> --json
```

---

### Step 5 — Pull open tasks linked to the deal

```bash
attio tasks list --not-completed --linked-object deals --json
```

Filter client-side to tasks where `linked_records[].target_record_id == DEAL_ID`.

Note any tasks that are overdue (deadline in the past). These signal dropped follow-ups.

---

### Step 6 — Load LeadGrow context

Before diagnosis, load the following context files. These define what good looks like and what LeadGrow can offer.

```
leadgrow-hq/company/voice-guide.md      — tone and writing rules for all outreach
leadgrow-hq/company/ICP.md              — who we target, what their pain looks like
leadgrow-hq/company/offerings.md        — what we sell, how we position it
```

Do not summarize these. Read them in full. They are the benchmark for the diagnosis and draft.

---

### Step 7 — Diagnose the deal

Analyze the deal state across four dimensions:

**1. Time in stage**
Calculate `days_in_stage = today - stage_entered_at`. Flag deals where:
- Discovery > 7 days with no next call scheduled
- Proposal Sent > 5 days with no response noted
- Negotiation > 10 days with no update
- Any stage > 21 days with no activity

**2. Last activity**
Find the most recent note across deal + person records. Calculate days since that note. If last activity > 14 days: deal is cold. If > 30 days: deal is likely dead — say so.

**3. What's been discussed**
Read all notes and extract:
- The prospect's stated pain (what they told us is broken)
- Their stated timeline or urgency signals ("Q2 starts May 1", "need results by summer")
- Objections or friction points raised ("not sure about budget", "want to think it over")
- Commitments made on either side ("I'll send the case study", "they'll loop in their VP")
- Anything left unresolved or unanswered

**4. What's missing or blocking**
Identify the specific gap preventing the deal from advancing:
- Missing information from the prospect (decision-maker name, budget, timeline)
- LeadGrow deliverable not yet sent (proposal, case study, sequence sample)
- Waiting on a decision with no agreed deadline
- Overdue task that was never actioned
- No next meeting scheduled

---

### Step 8 — Recommend the next action

Based on the diagnosis, recommend one specific next action. Do not give a list of options. Pick the right move.

Use the recommendation logic below to decide.

Draft the outreach or talking points for that action. See [Drafting Rules](#drafting-rules).

---

### Step 9 — Present for review

Display the deal brief and recommendation to Mitch. Wait for his input before any write operation.

See [Review Interface](#review-interface) for the display format.

---

### Step 10 — Execute on approval

Once Mitch approves (with or without edits):

1. Create a task in Attio with the next action and a deadline
2. If the message is approved for sending: queue it in EmailBison
3. If Mitch wants to update the deal stage: run the stage update command
4. Confirm what was written back to Attio

---

## Recommendation Logic

Work through these in order. The first one that applies is the correct recommendation.

| Condition | Recommended Action |
|-----------|-------------------|
| Overdue task exists on the deal | Action the overdue task first. Name it explicitly. |
| Commitment was made by LeadGrow and not fulfilled | Fulfill it. Draft the deliverable or the message sending it. |
| Prospect asked a question in the last note that was never answered | Answer it. Draft the response. |
| Proposal was sent > 5 days ago with no reply | Follow up on the proposal. Draft a short check-in. |
| Discovery call happened, no proposal sent | Recommend sending proposal. Draft it or flag that generate-proposal skill should run. |
| First touch made, no call scheduled | Recommend booking the discovery call. Draft the scheduling message. |
| Last activity > 14 days, deal in active stage | Soft re-engagement. Draft a reason-to-reach-out message. |
| Last activity > 30 days, no urgency signals | Flag the deal as likely cold. Recommend a final bump or closing it out. |
| Deal is in Negotiation with no timeline | Recommend creating a mutual action plan. Draft a "here's what next 2 weeks look like" message. |
| Deal is in Won or Lost | Don't recommend an outreach action. Recommend archiving or requesting a case study (Won) or logging the loss reason (Lost). |

When no condition applies cleanly: read the last note and draft whatever the natural next human response to it would be.

---

## Drafting Rules

All outreach drafts must follow the LeadGrow voice guide. Non-negotiable rules:

- **No dashes** of any kind — no em-dash (—), no double-hyphen (--). Use periods or short sentences instead.
- **Lead with their situation, not ours.** Open with something specific to them from the notes.
- **Short.** 4-6 sentences for a follow-up. 8-10 for a re-engagement. Never longer unless it is a proposal or a formal response to a multi-part question.
- **One ask.** End with exactly one clear request (a yes/no question, a specific meeting time, a decision point). Never two asks in one message.
- **No fluff openers.** Never start with "Hope you're well", "Just checking in", or "Following up on my last email."
- **Reference specifics.** Use their name, their company name, something from the notes. Generic messages read as mass emails.
- **Match the context.** If the deal is warm and recent: direct. If it's been 3 weeks: acknowledge the gap, give them a reason to reply.

For talking points (pre-call prep): bullet format is fine. 3-5 key points Mitch should hit, 2-3 questions to ask, any objections to expect based on the notes.

---

## Review Interface

Claude displays this before asking for input:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEAL: <deal_name>
Company: <company_name>   Contact: <name> (<email>)
Stage: <stage>   In stage: <N> days   Last activity: <N> days ago
Value: <value or "not set">
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SITUATION SUMMARY
<2-4 sentence summary of where the deal is and how it got here.
Based strictly on the notes. No invented context.>

WHAT'S BEEN DISCUSSED
<Bulleted extract: key pain points, signals, objections, open questions, commitments>

BLOCKERS
<Specific gap preventing the deal from advancing. One clear sentence.>

DIAGNOSIS
<One sentence: what this deal actually needs right now.>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED NEXT ACTION
<Action verb + what to send/do + by when>

DRAFT
─────────────────────────────────────────────────────────────
<The email, message, or talking points. Full draft. Ready to use or edit.>
─────────────────────────────────────────────────────────────

What do you want to do?

  [a] Approve — create task + queue message as-is
  [e] Edit draft — paste your version, then approve
  [d] Different action — tell me what you want instead
  [s] Stage update only — advance the stage without sending
  [skip] Skip this deal for now
```

Wait for input. Do not proceed until Mitch responds.

---

## User Actions

### [a] Approve

Create the task and (if a message is part of the action) queue it in EmailBison.

```bash
# Create task linked to the deal
attio tasks create \
  --content "<recommended_action>" \
  --deadline "<ISO_8601_deadline>" \
  --linked-record '{"target_object": "deals", "target_record_id": "<DEAL_ID>"}' \
  --json
```

If sending a message via EmailBison, route through the `outbound:queue-message` skill. Do not call EmailBison directly from this skill.

### [e] Edit draft

Mitch pastes the edited version. Claude confirms the edit is captured, then runs the same approve flow with the edited text.

### [d] Different action

Mitch states what he actually wants to do. Claude drafts for that action and presents a new review block. Do not loop more than twice — if Mitch redirects twice, just ask him to specify the exact text to use.

### [s] Stage update only

```bash
attio records update deals <DEAL_ID> \
  --values '{"stage": "<new_stage>"}' \
  --json
```

Confirm the update. No task creation unless Mitch requests it.

### [skip]

Log nothing. Move to the next deal (in pipeline review mode) or exit (in single-deal mode).

---

## Output

On completion of each deal, print a summary line:

```
Dealt — <deal_name>: <action taken>
  Task: "<task_content>" due <deadline>  [task_id]
  Message: queued in EmailBison  [or "not sent"]
  Stage: <updated_stage>  [or "unchanged"]
```

In pipeline review mode (`--all-active`), print a session summary at the end:

```
PIPELINE REVIEW COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<N> deals reviewed
<N> tasks created
<N> messages queued
<N> deals flagged as cold
<N> skipped
```

---

## Context Files to Load

Load these before Step 7 (Diagnosis). Read in full.

| File | Why |
|------|-----|
| `leadgrow-hq/company/voice-guide.md` | Draft outreach in Mitchell's voice. Non-negotiable. |
| `leadgrow-hq/company/ICP.md` | Understand what good-fit pain looks like. Helps calibrate urgency and blockers. |
| `leadgrow-hq/company/offerings.md` | Know what we can offer at each stage. Needed if recommending a proposal or scoping a follow-up. |

---

## CLI Commands Used

| Command | Purpose |
|---------|---------|
| `attio deals search "<name>" --json --limit 5` | Find deal by name |
| `attio people search "<email>" --json --limit 3` | Find person by email to resolve linked deals |
| `attio records list deals --filter <json> --json` | List deals linked to a person |
| `attio records get deals <DEAL_ID> --json` | Pull full deal record |
| `attio records get people <PERSON_ID> --json` | Pull linked contact details |
| `attio records get companies <COMPANY_ID> --json` | Pull linked company details |
| `attio notes list --parent-object deals --parent-record-id <id> --json` | All notes on the deal |
| `attio notes list --parent-object people --parent-record-id <id> --json` | Notes on the linked person |
| `attio tasks list --not-completed --linked-object deals --json` | Open tasks (filter client-side by deal ID) |
| `attio tasks create --content <text> --deadline <iso8601> --linked-record <json> --json` | Create next-action task |
| `attio records update deals <DEAL_ID> --values <json> --json` | Update deal stage |

---

## AI Role

Clear division of labor:

| Responsibility | Claude | CLI |
|----------------|--------|-----|
| Resolve deal from name or email | Yes (decides which command to run) | No |
| Filter tasks to target deal (client-side) | Yes | No |
| Read notes and synthesize situation | Yes | No |
| Apply recommendation logic | Yes | No |
| Draft outreach in LeadGrow voice | Yes | No |
| Display review interface and wait for input | Yes | No |
| Convert natural language deadlines to ISO 8601 | Yes | No |
| Execute all API writes (tasks, stage updates) | No | Yes |
| Handle auth, retries, rate limiting | No | Yes |
| Route messages to EmailBison | Delegates to outbound:queue-message skill | No |

---

## Example Invocation

### Single deal — by contact email

```
User: "What's next with the Storylane deal?"

Claude: Searches for deals linked to storylane.io or the known contact email.
Pulls deal record, notes, open tasks.
Loads voice + ICP + offerings.
Diagnoses: Proposal was sent 8 days ago. No reply. One open task (overdue by 3 days): "Follow up on proposal."
Recommends: Follow up on proposal with a specific hook from the discovery call notes.
Drafts the message.
Presents review interface.
Mitch: [a]
Claude: Creates task "Follow up on proposal — 2026-04-03" linked to Storylane deal. Queues message.
Prints: Dealt — Storylane: task created + message queued.
```

### Pipeline review — all active deals

```
User: "Let's do the pipeline review."

Claude: Runs attio records list deals (all non-Won, non-Lost) --json.
Works through each deal one at a time.
For each: pulls notes, tasks, diagnoses, recommends, presents review block.
Mitch approves, edits, or skips each.
After all deals: prints session summary.
```

### Pre-call prep — talking points only

```
User: "Prep me for my call with Tensorlake at 2pm."

Claude: Pulls Tensorlake deal record and all notes.
Diagnosis: They asked about our reporting cadence and wanted a sample report. That was 5 days ago and never sent.
Recommendation: Bring a sample report to the call. Cover their reporting question directly. Push for a decision or a scoped trial.
Draft: 5 talking points + 3 questions to ask + 2 objections to expect.
No task is created unless Mitch approves post-call.
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No deal found for identifier | Surface the exact search used, return zero-results message, ask for a more specific identifier. Do not guess. |
| Multiple deals match the identifier | List all matches (name, stage, contact) and ask Mitch to pick one. |
| Deal has no notes | Flag it. Diagnosis proceeds with "no prior history" noted. Recommendation defaults to "schedule discovery call" or "make first contact" depending on stage. |
| Deal is Won or Lost | State the outcome and do not recommend outreach. Offer: log a loss reason (Lost) or request a case study (Won). |
| Voice guide or offerings file missing | Halt and report the missing file path. Do not draft without the voice guide. |
| `attio tasks create` fails | Log the error and the task content. Ask Mitch if he wants to retry or note it manually. Do not silently skip. |
| Stage update fails | Surface the error. The task may still be created. Report both outcomes separately. |
