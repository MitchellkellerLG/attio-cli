---
name: pipeline-snapshot
description: >
  One-command pipeline health check. Pulls all active deals from Attio, calculates days inactive
  from last note, groups by stage, flags stale/cold/dead deals, and renders a ranked summary
  table with total pipeline value and stage breakdown. Use for weekly reviews, Monday morning
  check-ins, or anytime you need the full picture without drilling into individual deals.
  Supports --stage to filter by pipeline stage, --stale-days to customize the inactivity
  threshold, and --export to save the snapshot to a file.
  Triggers: show me the pipeline, pipeline snapshot, pipeline health, pipeline overview,
  how's the pipeline, what's in the pipeline, deal overview, weekly pipeline review,
  Monday morning pipeline, pipeline status, pipeline report.
version: 0.1.0
maturity: draft
triggers:
  - pipeline snapshot
  - show me the pipeline
  - pipeline health
  - pipeline overview
  - how's the pipeline
  - what's in the pipeline
  - deal overview
  - weekly pipeline review
  - Monday morning pipeline
  - pipeline status
  - pipeline report
  - what deals are active
  - show deals
---

# Skill: pipeline-snapshot

Full pipeline health in one shot. Every active deal, ranked by urgency, with stage distribution and total value.

---

## When to Use

- **Monday morning** -- "what does the pipeline look like?"
- **Weekly review** -- scan everything before drilling into specific deals with deal-next-step
- **Before a team call** -- get the numbers without digging through Attio's UI
- **Pipeline gut check** -- "are we healthy or are things rotting?"

---

## Inputs

All optional. No inputs = show everything.

| Input | Type | Notes |
|-------|------|-------|
| `--stage` | string | Filter to a single stage (e.g., "Discovery", "Proposal Sent") |
| `--stale-days` | integer | Override inactivity threshold (default: 7 days) |
| `--export` | flag | Save snapshot to `temp/scratch/pipeline-snapshot-YYYY-MM-DD.md` |

---

## What Claude Does

### Step 1 -- Pull all deals

```bash
attio deals list --all --json
```

Extract from each deal:
- `record_id`
- `name` (display name)
- `stage` (current pipeline stage)
- `value` (deal value if set)
- `owner` (assigned user if set)

Filter out deals where stage is "Won" or "Lost" unless `--stage` explicitly requests them.

---

### Step 2 -- Pull linked companies

For each deal, extract the linked company record ID from the deal's values. Batch the unique company IDs and fetch:

```bash
attio records get companies <COMPANY_ID> --json
```

Cache by company ID to avoid duplicate fetches. Extract company name.

---

### Step 3 -- Pull last activity per deal

For each deal, fetch the most recent note:

```bash
attio notes list --parent-object deals --parent-record-id <DEAL_ID> --limit 1 --json
```

Extract `created_at` from the most recent note. If no notes exist, mark as "No activity on record."

Calculate `days_inactive = today - most_recent_note.created_at`.

---

### Step 4 -- Classify deal health

Apply these thresholds (or `--stale-days` override):

| Status | Condition |
|--------|-----------|
| Hot | `days_inactive` <= 3 |
| Active | `days_inactive` 4-7 |
| Stale | `days_inactive` 8-14 |
| Cold | `days_inactive` 15-30 |
| Dead | `days_inactive` > 30 or no notes exist |

---

### Step 5 -- Pull open tasks per deal

```bash
attio tasks list --not-completed --linked-object deals --linked-record-id <DEAL_ID> --json
```

Count open tasks. Flag any that are overdue (deadline in the past).

---

### Step 6 -- Render the snapshot

Display in this exact format:

```
PIPELINE SNAPSHOT -- [DATE]
================================================================

SUMMARY
  Total active deals: [N]
  Total pipeline value: $[X]
  Deals needing action: [N] (stale + cold + dead)
  Overdue tasks: [N]

BY STAGE
  Discovery:      [N] deals   $[value]   avg [X] days inactive
  Proposal Sent:  [N] deals   $[value]   avg [X] days inactive
  Negotiation:    [N] deals   $[value]   avg [X] days inactive
  [other stages as they appear]

================================================================
DEALS BY URGENCY
================================================================

[Dead] Acme Corp -- Discovery -- $5,000
  Last activity: 45 days ago (No notes since Feb 20)
  Open tasks: 2 (1 overdue)
  >> This deal is likely dead. Close or re-engage.

[Cold] Widget Inc -- Proposal Sent -- $12,000
  Last activity: 22 days ago
  Open tasks: 0
  >> No follow-up after proposal. Needs a check-in.

[Stale] Foo Labs -- Negotiation -- $8,000
  Last activity: 10 days ago
  Open tasks: 1
  >> Slipping. Task exists but no recent movement.

[Active] Bar Systems -- Discovery -- $3,000
  Last activity: 5 days ago
  Open tasks: 1

[Hot] Baz Co -- Proposal Sent -- $15,000
  Last activity: 1 day ago
  Open tasks: 0

================================================================
```

Rules for the urgency notes (the `>>` lines):
- Only show for Stale, Cold, and Dead deals
- Be specific and actionable, not generic
- Reference the stage and what's missing (no follow-up, no tasks, overdue task)
- One sentence max

Sort order: Dead first (most urgent), then Cold, Stale, Active, Hot. Within each tier, sort by value descending.

---

### Step 7 -- Export (if --export)

Write the full snapshot to `temp/scratch/pipeline-snapshot-YYYY-MM-DD.md`.

Print the file path when done.

---

### Step 8 -- Offer drill-down

After displaying the snapshot, ask:

```
Want to drill into any of these? Name a deal or say "run deal-next-step on [deal]".
```

If Mitch names a deal, hand off to the deal-next-step skill with that deal's record ID.

---

## Optimizations

**Batch where possible.** Don't make 50 sequential API calls when you can parallelize.

- Fetch all deals in one `--all` call
- Group note fetches. If you have 15 deals, make 15 calls, not 15 rounds of back-and-forth with the user.
- Cache company lookups. Most deals from the same company share a company ID.

**Handle missing data gracefully:**
- Deal with no value set: show "not set" instead of $0
- Deal with no linked company: show "No company linked"
- Deal with no notes: show "No activity on record" and classify as Dead
- Deal with no stage: show "No stage" (shouldn't happen but don't crash)

---

## Context Files to Load

None required. This is a data pull, not a copy-writing skill.

If Mitch asks to draft outreach from the snapshot, hand off to deal-next-step which loads voice-guide.md, ICP.md, and offerings.md.

---

## CLI Commands Used

| Command | Purpose |
|---------|---------|
| `attio deals list --all --json` | Pull all deal records |
| `attio records get companies <id> --json` | Resolve linked company names |
| `attio notes list --parent-object deals --parent-record-id <id> --limit 1 --json` | Last activity per deal |
| `attio tasks list --not-completed --linked-object deals --linked-record-id <id> --json` | Open tasks per deal |

---

## AI Role

- **Claude pulls the data, does the math, renders the table.** No judgment calls needed from Mitch until the snapshot is displayed.
- **Urgency notes are Claude's opinion.** Be direct. "This deal is likely dead" is better than "This deal may benefit from re-engagement."
- **Don't summarize what Mitch can read.** The table IS the output. Don't follow it with a paragraph restating the numbers.

---

## Example Invocation

**Full pipeline check:**
```
"Show me the pipeline"
```
Claude pulls all deals, renders the snapshot, offers drill-down.

**Filtered by stage:**
```
"Show me everything in Proposal Sent"
```
Claude filters to Proposal Sent stage only, same format.

**With custom threshold:**
```
"Pipeline snapshot, flag anything inactive for 5+ days"
```
Claude uses 5-day threshold instead of default 7.

**Export for Monday standup:**
```
"Pipeline snapshot, export it"
```
Claude renders to screen AND saves to `temp/scratch/pipeline-snapshot-YYYY-MM-DD.md`.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No deals found | Print "No active deals in pipeline." and stop |
| No deals match --stage filter | Print "No deals in [stage] stage." and stop |
| API auth fails | Print auth error, suggest `attio config set api-key` |
| Single deal fetch fails | Skip that deal, note it in output: "[Deal name] -- failed to fetch notes" |
| Rate limited | Attio CLI handles retry/backoff automatically |

---

## Handoff to deal-next-step

When Mitch picks a deal from the snapshot, pass:
- `deal_name` or `record_id` (whichever was used to identify it)
- Skip re-fetching data Claude already has (deal record, company, last note timestamp)

This avoids duplicate API calls when going from snapshot to deep-dive.
