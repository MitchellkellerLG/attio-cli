---
title: Weekly Nurture Run
type: workflow
created: 2026-04-01
estimated-time: 30-45 minutes
tools:
  - attio-cli (lists list, lists entries list)
  - lead-nurture skill
---

# Weekly Nurture Run

Touch every stale prospect across your active pipeline lists before they go cold. Run this every Friday afternoon or Monday morning — one session, all the lists that matter, prioritized by how long each contact has been silent.

The rule: if a prospect hasn't heard from you in more than a week, they've mentally moved on. This workflow catches them before that happens.

---

## Prerequisites

- `attio` CLI installed and authenticated
- Pipeline lists exist in Attio (Nurture, Interested - No Response, Proposal Sent, or equivalents)
- Voice guide and ICP at `leadgrow-hq/company/voice-guide.md` and `leadgrow-hq/company/ICP.md` (the skill loads these automatically)
- EmailBison accessible via `bison_mcp` MCP (for queuing approved messages)

---

## Step-by-Step

### Step 1 — Pull all list names (2 min)

```bash
attio lists list --json
```

**Example output:**

```json
{
  "data": [
    { "id": { "list_id": "lst_abc001" }, "name": "Nurture", "api_slug": "nurture" },
    { "id": { "list_id": "lst_abc002" }, "name": "Interested - No Response", "api_slug": "interested_no_response" },
    { "id": { "list_id": "lst_abc003" }, "name": "Proposal Sent", "api_slug": "proposal_sent" },
    { "id": { "list_id": "lst_abc004" }, "name": "Closed Won", "api_slug": "closed_won" },
    { "id": { "list_id": "lst_abc005" }, "name": "Q2 Outbound Pipeline", "api_slug": "q2_outbound_pipeline" }
  ]
}
```

---

### Step 2 — Identify nurture-relevant lists (1 min)

Not all lists need nurturing. Apply this filter:

**Include (nurture-relevant):**
| List Name | Why Included | Recommended --days Threshold |
|-----------|--------------|------------------------------|
| Nurture | Actively cultivating. Goes cold fastest. | 7 days |
| Interested - No Response | They showed interest but stopped replying. High priority. | 7 days |
| Proposal Sent | Sent a proposal, waiting on a decision. Short window before they forget. | 5 days |
| Demo Booked / Meeting Scheduled | Pre-call or post-no-show follow-up needed. | 3 days |
| Warm Leads | Identified as ICP, not yet contacted or in early stage. | 14 days |
| Reactivation | Previously closed or stale. Touch infrequently. | 21 days |

**Exclude (don't nurture):**
- Closed Won
- Closed Lost
- Unsubscribed / Do Not Contact
- Any list with "Archive" or "Old" in the name
- Outbound Pipeline (active campaigns already running in EmailBison — don't double-touch)

**Decision tree:**
```
For each list returned by attio lists list:
├── Name contains "Won", "Lost", "Archive", "Unsubscribed" → EXCLUDE
├── Name contains "Nurture", "Interested", "Proposal", "Warm" → INCLUDE
├── Active campaign running in EmailBison for this list → EXCLUDE (avoid double-touch)
└── Unsure → include with conservative threshold (14 days)
```

---

### Step 3 — Run lead-nurture skill across relevant lists (25-35 min)

**Single list:**

```
Run lead-nurture for the Interested - No Response list, 7 day threshold.
```

**Multi-list (recommended for weekly run):**

```
Run lead-nurture across Nurture, Interested - No Response, and Proposal Sent lists.
Use 7 days for Nurture and Interested, 5 days for Proposal Sent.
```

The skill handles sequential processing: finishes one list, prints a mini-summary, moves to the next.

**Per-contact review loop (what you'll see for each contact):**

```
────────────────────────────────────────────────
CONTACT 1 OF 7 — Nurture list
────────────────────────────────────────────────
NAME:      Jordan Lee
TITLE:     VP of Sales
COMPANY:   Boundless
LAST TOUCH: 14 days ago (2026-03-17)

HISTORY SUMMARY:
  • 2026-03-10: Intro call. Interested in cold email for SMB segment.
                Asked about EmailBison pricing. Said to follow up in 2 weeks.
  • 2026-03-17: Sent pricing deck. No reply.

DRAFT MESSAGE:
Subject: pricing question

Jordan — wanted to check if you had a chance to look through the deck.
Most teams in your space are running 3-4 sequences by month two.
Happy to walk through what that looks like for Boundless specifically.

Worth a quick call this week?

— Mitch
────────────────────────────────────────────────
[a] Approve and queue  [e] Edit  [s] Skip  [r] Remove  [q] Quit
```

**Action guide:**
- `[a]` — approve, queues to EmailBison + creates Attio task due in 5 business days
- `[e]` — edit the message, then approve
- `[s]` — skip this contact, leave on list (use when recently touched outside Attio)
- `[r]` — remove from list (disqualified, wrong ICP, dead opportunity)
- `[q]` — stop session, get summary of what was processed

---

### Threshold guidance by list type

| List | Recommended --days | Reasoning |
|------|-------------------|-----------|
| Nurture | 7 | These are warm-ish contacts. Weekly cadence keeps the relationship alive. |
| Interested - No Response | 7 | They signaled interest. Short window before they move to a competitor. |
| Proposal Sent | 5 | Proposals go cold fast. 5 days without a reply = follow up immediately. |
| Demo Booked | 3 | If they no-showed or need a rescheduled, reach out same day or next. |
| Warm Leads | 14 | Still being cultivated. Bi-weekly touch is enough. |
| Reactivation | 21 | Lower priority, lower frequency. Don't over-touch dead opportunities. |

---

### Handling long-stale contacts (21+ days)

The skill flags contacts with no activity in 21+ days with a `[Long-stale — verify still relevant]` warning.

**Decision tree for long-stale contacts:**

```
Contact last touched 21+ days ago?
├── They were previously interested but timing was bad → Send a re-engagement message
│   ("It's been a few weeks — wanted to check if timing has changed.")
├── They went completely silent after a positive first call → One final bump
│   ("One last note before I close this out on my end.")
├── You've sent 3+ messages with zero reply → Remove from list
│   (Not removing them just clutters your pipeline. Remove and log why.)
└── The opportunity is dead (company changed, role changed, competitor won) → Remove
```

**For long-stale contacts, the skill will still generate a draft**, but it will be lighter and either a re-engagement or a "final bump" tone. Review these individually — don't bulk-approve them.

---

### Step 4 — Review session summary

At the end of each list, the skill prints a summary:

```
────────────────────────────────────────────────
NURTURE SESSION COMPLETE — 2026-04-01
────────────────────────────────────────────────
List:     Nurture
Reviewed: 7 contacts
Approved: 4 (messages queued to EmailBison, tasks created in Attio)
Skipped:  2
Removed:  1
────────────────────────────────────────────────
```

After all lists (multi-list mode):

```
MULTI-LIST NURTURE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nurture:                   4 approved, 1 skipped
Interested - No Response:  3 approved, 2 skipped
Proposal Sent:             2 approved, 1 removed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 9 messages queued, 9 tasks created
```

---

## Friday vs Monday Timing

**Friday afternoon (preferred):**
- Messages queue in EmailBison, go out Monday morning when prospects are back at their desks
- You review the week's cold pipeline before weekend — nothing slips into a second week of silence
- Inbox recovery is easier on Monday when replies are already waiting

**Monday morning:**
- Good if Friday got chaotic
- Run before checking email — do the proactive outbound first, then respond reactively
- Skip the morning pipeline review if you're also doing this — they overlap significantly (Monday morning is both overdue tasks AND nurture)

**Avoid:** Mid-week (Tue-Thu) for the full nurture run. It creates inconsistent cadence and you'll run into the same contacts again too soon.

---

## Speed Mode: Export First, Review Later

If you're short on time, generate all drafts to a file and review them asynchronously:

```
Run lead-nurture for Nurture and Interested - No Response lists — export to file.
```

Drafts go to:
- `C:/Users/mitch/Everything_CC/temp/scratch/nurture-Nurture-2026-04-01.md`
- `C:/Users/mitch/Everything_CC/temp/scratch/nurture-Interested - No Response-2026-04-01.md`

Review both files during a break. Copy-paste messages you want to send manually, delete what doesn't fit, add any others to Attio tasks manually.

Downside: No EmailBison queueing, no automatic Attio task creation. Export mode is a safety valve, not the primary workflow.

---

## Done Criteria

The weekly nurture run is complete when:

1. Every contact on the Nurture and Interested - No Response lists who has been silent for 7+ days has been reviewed (approved, skipped with reason, or removed)
2. Every contact on the Proposal Sent list silent for 5+ days has been reviewed
3. All approved messages are queued in EmailBison
4. All approved contacts have a follow-up task in Attio due within 5 business days
5. Long-stale contacts (21+ days) have been individually reviewed and either actioned or removed

---

## Common Errors

**"No list matching 'Nurture' found"**
The skill is case-insensitive but needs an exact name match. Run `attio lists list --json` to see exact list names in your workspace. Common variations: "Nurture Pool", "Lead Nurture", "To Nurture".

**"No contacts meet the criteria — all contacts have been touched recently"**
Good problem to have. Either the nurture run last week worked, or you're running too frequently for the threshold. Confirm the `--days` threshold makes sense for your current cadence.

**Contact has no email address on record**
The skill flags this as `[No email on record — cannot queue to EmailBison]`. The draft is still shown. Options:
- `[e]` edit to add context, approve and add the email to Attio manually, then queue from EmailBison directly
- `[r]` remove from list if you can't contact them
- `[s]` skip and add their email to the Attio record manually, then re-run next week

**EmailBison queue fails (bison_mcp error)**
The message draft is still generated. Approve it and the draft is saved locally. Send manually from `temp/scratch/`. The Attio task is still created.

**Rate limiting (429) mid-session**
The `attio-cli` tenacity retry layer handles this automatically. If it exhausts retries, the session stops and prints a summary of what was completed before the error. Re-run with `--limit` to process remaining contacts.
