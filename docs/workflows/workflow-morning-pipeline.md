---
title: Morning Pipeline Review
type: workflow
created: 2026-04-01
estimated-time: 15-20 minutes
tools:
  - attio-cli
  - overdue-follow-up skill
  - deal-next-step skill
---

# Morning Pipeline Review

Clear follow-up debt and advance stuck deals before new work enters. Run this every weekday morning as the first 15-20 minutes of your session. The goal: zero unaddressed overdue tasks, every active deal with a confirmed next-action task.

This workflow is sequential. Do the overdue tasks first — they represent dropped balls that compound daily. Then sweep the deal pipeline for anything that's gone quiet.

---

## Prerequisites

- `attio` CLI installed and authenticated (`ATTIO_API_KEY` set)
- Claude Code session open with access to `overdue-follow-up` and `deal-next-step` skills
- Voice guide and ICP loaded (both skills handle this automatically)

---

## Step-by-Step

### Step 1 — Pull overdue task count (1 min)

```bash
attio tasks list --not-completed --json
```

Parse the response client-side for tasks where `deadline_at` is non-null and `deadline_at < now()`.

**Expected output:**

```
[
  {
    "id": { "task_id": "task_abc123" },
    "content": "Follow up on pricing deck",
    "deadline_at": "2026-03-29T00:00:00.000Z",
    "linked_records": [{ "target_object": "deals", "target_record_id": "rec_xyz" }]
  },
  ...
]
```

Count the overdue tasks. If zero, skip to Step 3.

---

### Step 2 — Clear overdue follow-ups (5-10 min, if any exist)

If overdue tasks were found in Step 1, run the `overdue-follow-up` skill:

```
Run overdue follow-up skill
```

**Decision tree:**

```
Overdue tasks found?
├── YES → Run overdue-follow-up skill
│         For each task Claude surfaces:
│         ├── [a] Approve → task deadline pushed +7d, note logged, message printed
│         ├── [e] Edit → revise draft, then approve
│         ├── [c] Mark complete → task closed (work was already done)
│         ├── [s] Skip → leave overdue, move on (use sparingly)
│         └── [d] Done for today → stop early, get summary
│
└── NO → Skip to Step 3
         Print: "No overdue tasks. Pipeline is clean."
```

**Time estimate:** 1-2 minutes per contact depending on edit needed. A queue of 5 contacts = ~8 minutes.

**If the queue is large (10+ contacts):** Start with `--limit 5` to clear the worst offenders first. You can re-run tomorrow for the rest.

```
Run overdue follow-up skill with limit 5
```

**Tip:** Use `[b]` (bulk approve remaining) once you've reviewed the first 2-3 and trust the queue. Claude generates copy; you approved the first few and confirmed the pattern is right.

---

### Step 3 — Pull active deals (1 min)

```bash
attio deals list --json
```

Filter client-side to exclude deals where `stage` equals "Closed Won" or "Closed Lost". You want only deals in active stages (Discovery, Proposal Sent, Negotiation, Interested, etc.).

**Example response shape:**

```json
{
  "data": [
    {
      "id": { "record_id": "rec_deal_001" },
      "values": {
        "name": [{ "value": "Acme Corp" }],
        "stage": [{ "status": { "title": "Proposal Sent" } }]
      }
    }
  ]
}
```

For each active deal, also pull the most recent note timestamp to identify stale deals:

```bash
attio notes list --parent-object deals --parent-record-id <deal_id> --limit 1 --json
```

**Flag any deal where the most recent note is older than 7 days.** These are the ones that need a next-step decision today.

---

### Step 4 — Run deal-next-step for stale deals (3-5 min per deal)

For each deal flagged as stale (last activity > 7 days):

```
What's next with the [Deal Name] deal?
```

Or for a full pipeline sweep:

```
Let's do the pipeline review.
```

**Decision tree:**

```
Stale deal identified (last activity > 7 days)?
├── YES → Run deal-next-step skill for that deal
│         Claude surfaces: situation summary, blockers, recommendation, draft
│         ├── [a] Approve → task created in Attio + message queued to EmailBison
│         ├── [e] Edit draft → revise, then approve
│         ├── [d] Different action → redirect Claude to a different next move
│         ├── [s] Stage update only → advance stage without sending a message
│         └── [skip] → skip this deal, no action taken
│
└── NO (last activity < 7 days) → No action needed. Deal has active momentum.
```

**Time estimate:** 3-5 minutes per stale deal including reading the brief and approving/editing the draft.

**If you have 3+ stale deals:** Use pipeline review mode to triage all at once before diving into individual briefs:

```
Let's do the pipeline review.
```

Claude generates a triage table (red/yellow/green) before any individual deal. You can select specific deals or bulk-approve obvious actions.

---

## Done Criteria

The morning review is complete when:

1. **Zero unaddressed overdue tasks** — every overdue task has been approved (message drafted), marked complete, or consciously skipped with a reason
2. **Every active deal has a next-action task** in Attio with a real deadline — not a vague "follow up someday" but a specific action due within 7 days
3. **No active deal has been silent for more than 7 days** without a deliberate decision made this session

If you hit the time limit (20 min) before finishing: stop, note where you left off. Tomorrow's overdue-follow-up run will catch whatever slipped.

---

## Common Errors

**"ATTIO_API_KEY not set or invalid"**
Run `attio config set api-key <your_key>` or export the env var before starting.

**Zero deals returned but you know you have active deals**
The `deals list` command may need a different filter or your deals are under a different object slug. Try `attio objects list --json` to confirm the correct slug for your workspace.

**Overdue-follow-up skill shows a contact with no notes**
This happens when a task was created but no call or interaction was ever logged. Claude will flag it as `[No history — first touch]`. Treat it as a cold touch: approve a short, light message or mark the task complete if the opportunity is dead.

**deal-next-step can't find a deal by name**
Deals in Attio are searched by their record name. If the deal is named "Acme — Q2 Expansion" but you searched "Acme Corp", it won't match. Provide the exact deal name or the linked contact's email instead:

```
What's next with the Acme deal? Contact email is sarah@acme.com
```

---

## Example Session

```
Session start: 8:45am

Step 1: attio tasks list --not-completed --json
Result: 4 overdue tasks (3 on deals, 1 on a person)

Step 2: Run overdue-follow-up skill
- Jordan Lee (Boundless) — Overdue 7d → [a] Approved. Message printed. Task deadline pushed.
- Sarah Chen (Acme) — Overdue 3d → [e] Edited (made it shorter). Approved.
- Marcus Webb (Storylane) — Overdue 12d → [c] Marked complete (sent manually yesterday, forgot to update)
- Priya Nair (Tensorlake) — Overdue 1d → [a] Approved.

Step 3: attio deals list --json
Result: 6 active deals. Notes check:
- Acme Corp — last note 8 days ago → FLAG
- Storylane — last note 2 days ago → OK
- Tensorlake — last note 5 days ago → OK
- Boundless — last note 14 days ago → FLAG
- Teachaid — last note 1 day ago → OK
- Aurium — last note 30 days ago → FLAG (likely cold)

Step 4: Run deal-next-step for Acme, Boundless, Aurium
- Acme: proposal follow-up drafted → approved, task created
- Boundless: re-engagement message → approved, task created
- Aurium: flagged as cold → [d] "Send a final bump" → drafted, approved

Session end: 9:05am
Total: 20 minutes. 4 follow-ups cleared. 3 deals actioned.
```
