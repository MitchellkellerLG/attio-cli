---
title: New Prospect Intake
type: workflow
created: 2026-04-01
estimated-time: 5-10 min per prospect, 30-45 min for bulk CSV (50+ rows)
tools:
  - attio-cli (people assert, companies assert, lists entries assert, notes create)
---

# New Prospect Intake

Get prospects into Attio correctly and immediately when a new batch arrives — from Clay export, EmailBison reply, manual add, or any other source. Right object, right list, right attributes, right intake note. No half-baked records.

This workflow is the gate before any outreach. A prospect not properly in Attio is a prospect you'll lose track of.

---

## Prerequisites

- `attio` CLI installed and authenticated
- Target list already exists in Attio (get its ID via `attio lists list --json`)
- For Clay exports: CSV with at minimum `email`, `first_name`, `last_name`, and optionally `company_name`, `job_title`, `linkedin_url`
- For EmailBison replies: reply details pulled from EmailBison (email, name, company if available)

---

## Minimum Required Fields

A person record in Attio is valid for outreach purposes if it has:

| Field | Attio Attribute Slug | Required? | Notes |
|-------|---------------------|-----------|-------|
| Email address | `email_addresses` | YES | Primary matching attribute. Without it, records duplicate. |
| Full name | `name` | YES | Use `full_name` format: `"First Last"` |
| Job title | `job_title` | Recommended | Used by lead-nurture and deal-next-step skills for persona filtering |
| Company | linked company record | Recommended | Assert separately, link via company record ID |

Everything else (LinkedIn URL, phone, enrichment data) is supplemental. Don't block intake waiting for it.

---

## Step-by-Step

### Step 1 — Check if person already exists (30 sec)

Always check before creating. Attio will deduplicate on `assert`, but checking first lets you decide whether to update vs. create.

```bash
attio people search --email "james.wu@storylane.io" --json
```

**By name (if no email yet):**

```bash
attio people search --query "James Wu" --json
```

**Expected response (found):**

```json
{
  "data": [
    {
      "id": { "record_id": "rec_01abc123" },
      "values": {
        "name": [{ "full_name": "James Wu" }],
        "email_addresses": [{ "email_address": "james.wu@storylane.io" }],
        "job_title": [{ "value": "Head of Growth" }]
      }
    }
  ]
}
```

**Decision tree:**

```
Search returns a result?
├── YES, exact email match → Use existing record_id. Skip to Step 4 (add to list).
│   Note: assert will update the record with any new field values you provide.
├── YES, name match only, different email → Different person OR changed email.
│   Check the company and title. If same person: use existing record, update email.
│   If genuinely different person: proceed to Step 2 with their new email.
└── NO results → Proceed to Step 2 (create the record).
```

---

### Step 2 — Create or assert the person record (1-2 min)

Use `assert` with `email_addresses` as the matching attribute. This creates the record if it doesn't exist, or updates it if it does — idempotent and safe to run multiple times.

**Minimum viable assert (email + name):**

```bash
attio people assert \
  --matching-attribute email_addresses \
  --values '{"email_addresses": [{"email_address": "james.wu@storylane.io"}], "name": [{"full_name": "James Wu"}]}' \
  --json
```

**With job title and LinkedIn:**

```bash
attio people assert \
  --matching-attribute email_addresses \
  --values '{
    "email_addresses": [{"email_address": "james.wu@storylane.io"}],
    "name": [{"full_name": "James Wu"}],
    "job_title": [{"value": "Head of Growth"}],
    "linkedin_url": [{"value": "https://linkedin.com/in/jameswu"}]
  }' \
  --json
```

**Extract from response:** `data.id.record_id` — this is `PERSON_ID`. Save it. You'll use it in every subsequent command.

**Common mistakes:**

- `email_addresses` value must be an array of objects with the key `email_address` (not `email`):
  - WRONG: `"email_addresses": ["james.wu@storylane.io"]`
  - WRONG: `"email_addresses": [{"email": "james.wu@storylane.io"}]`
  - RIGHT: `"email_addresses": [{"email_address": "james.wu@storylane.io"}]`

- `name` value must use `full_name`, not `first_name`/`last_name` at the top level:
  - WRONG: `"name": "James Wu"`
  - WRONG: `"first_name": "James"` (this is not an Attio person attribute slug)
  - RIGHT: `"name": [{"full_name": "James Wu"}]`

---

### Step 3 — Create or assert the company (if applicable) (1 min)

Skip this step if:
- You have no company information
- The contact is a solo operator
- The company is already linked and confirmed on their existing record

Otherwise, assert the company using its domain as the matching attribute:

```bash
attio companies assert \
  --matching-attribute domains \
  --values '{"domains": [{"domain": "storylane.io"}], "name": [{"value": "Storylane"}]}' \
  --json
```

Extract `data.id.record_id` — this is `COMPANY_ID`.

If you only have the company name and no domain, use the name as matching attribute instead:

```bash
attio companies assert \
  --matching-attribute name \
  --values '{"name": [{"value": "Storylane"}]}' \
  --json
```

**Note:** Domain-based matching is more reliable. If the company already exists under `storylane.io`, it will return the existing record rather than create a duplicate.

After asserting the company, the link between person and company needs to be established in Attio. Check if this is handled automatically in your workspace setup via the `company` attribute on people records, or if you need to update the person record manually.

---

### Step 4 — Add to target list (30 sec)

```bash
attio lists entries assert \
  --list-id "lst_abc002" \
  --values '{"record_id": "rec_01abc123", "record_object": "people"}' \
  --json
```

To get the correct `list_id`, run `attio lists list --json` and find your target list by name.

**Example: add to "Interested - No Response" list:**

```bash
# First get the list ID
attio lists list --json
# Find "Interested - No Response" → list_id: "lst_def456"

# Then add the person
attio lists entries assert \
  --list-id "lst_def456" \
  --values '{"record_id": "rec_01abc123", "record_object": "people"}' \
  --json
```

If `assert` returns a 409 (already on the list), that's fine — idempotent behavior. The contact is already there.

---

### Step 5 — Log intake note (1-2 min)

Every intake needs a note. This is how future sessions know where the prospect came from and what's known about them at intake.

```bash
attio notes create \
  --parent-object people \
  --parent-record-id "rec_01abc123" \
  --title "Intake — 2026-04-01" \
  --content "Source: Clay export from Q2 Outbound batch. Enriched data: Head of Growth at Storylane, 200 employees, Series B. LinkedIn: linkedin.com/in/jameswu. ICP match: SaaS, outbound-relevant role, funded. No prior contact." \
  --json
```

**Intake note should include:**
- Source (Clay export, EmailBison reply, LinkedIn connection, referral, event)
- Any enrichment data you have (company size, funding, tech stack signals)
- ICP match assessment (why this person is worth pursuing)
- Prior contact status (cold, replied, met, referral)
- Any specific context that will shape the first outreach

---

### Step 6 — Create qualification task (optional, recommended for high-priority intake)

For prospects you want to act on immediately (ICP-perfect, replied to cold email, referral):

```bash
attio tasks create \
  --content "Qualify James Wu — review LinkedIn + company, personalize first outreach" \
  --deadline "2026-04-03T09:00:00.000Z" \
  --linked-record '{"target_object": "people", "target_record_id": "rec_01abc123"}' \
  --json
```

Skip this for bulk intake — you'll catch them in the nurture or overdue-follow-up workflow.

---

## Bulk Intake (CSV from Clay or EmailBison)

For batches of 10+ prospects from a Clay export or campaign reply list.

### Option 1 — Semi-automated with Claude

Paste the CSV data (or share the file path) and ask:

```
Add these prospects to Attio and the [list name] list. They're from a Clay export.
```

Claude will run Steps 1-5 sequentially for each row. It handles deduplication (assert is idempotent) and formats the `--values` JSON for each person.

**Expect:** 2-3 minutes per batch of 10 when running interactively. For 50 contacts, ~15-20 minutes.

**Rate limit note:** Attio's limit is 60 requests/minute. A full intake (search + assert person + assert company + list add + note) = ~5 API calls per contact. At 10 contacts/batch, that's 50 calls — fine. Don't run more than 10 contacts at once without a pause.

### Option 2 — Export to temp/, process in batches

For CSV files over 100 rows:

1. Save the export to `C:/Users/mitch/Everything_CC/temp/csv-staging/clay-export-2026-04-01.csv`
2. Process in batches of 20, run one batch, wait a minute, run the next
3. Track which rows are done (add a "Attio status" column to the CSV)

### Minimum CSV columns for bulk intake

| Column | Maps To | Required |
|--------|---------|----------|
| `email` | `email_addresses[0].email_address` | YES |
| `first_name` + `last_name` OR `full_name` | `name[0].full_name` | YES |
| `company_name` | Company assert `name` | Recommended |
| `company_domain` | Company assert `domains[0].domain` | Recommended (use instead of name for deduplication) |
| `job_title` | `job_title[0].value` | Recommended |
| `linkedin_url` | `linkedin_url[0].value` | Optional |

---

## Source-Specific Intake Notes

### Clay export

Source note: `"Source: Clay export — [campaign name], [date]. Enriched via Clay [table name]."`

Usually has company domain, job title, LinkedIn. High data quality. Set ICP assessment in the intake note.

### EmailBison reply marked Interested

Source note: `"Source: EmailBison reply — [campaign name]. Replied to: [email subject line]. Marked Interested [date]."`

This is a warm reply — they showed interest. Add them to the "Interested - No Response" list (not just "Nurture"). Create a qualification task immediately. Don't let these sit.

The n8n `reply-to-crm` workflow (`docs/workflows/n8n-reply-to-crm.md`) automates this path. If that workflow is running, this intake is handled automatically for Interested replies.

### Manual add (LinkedIn connection, referral, event)

Source note: `"Source: [LinkedIn / referral from X / event name]. Context: [how you met, what was discussed]."`

These are the highest-priority intakes. Create a qualification task in Step 6.

---

## Done Criteria

Intake is complete when:

1. Person record exists in Attio with at minimum email + name
2. Company record exists and is linked (if applicable)
3. Contact is on the correct target list
4. Intake note exists on the person record with source and context
5. Qualification task exists for high-priority contacts (ICP-perfect, warm replies)

Quick verification:

```bash
# Confirm record exists with correct fields
attio people get --id "rec_01abc123" --json

# Confirm list membership
attio lists entries list "lst_def456" --json | grep "rec_01abc123"

# Confirm note exists
attio notes list --parent-object people --parent-record-id "rec_01abc123" --json
```

---

## Common Errors

**`assert` returns 422 with "value does not match expected format"**
Almost always a JSON shape issue. The most common mistakes:
- Email must be `[{"email_address": "..."}]` not `["..."]`
- Name must be `[{"full_name": "First Last"}]` not `"First Last"`
- All attribute values are arrays of objects, never bare strings
- `domains` for companies: `[{"domain": "storylane.io"}]` not `["storylane.io"]`

**`lists entries assert` fails with 404**
The list ID is wrong or the list was deleted. Re-run `attio lists list --json` to get current IDs. List IDs are UUIDs and don't change, but confirm you're using the right one.

**Duplicate person records created**
Happens when you run `create` instead of `assert`, or when the email was different between two calls. Fix: search for both records, decide which one to keep, merge data manually in Attio UI, and delete the duplicate. Going forward: always use `assert` with `--matching-attribute email_addresses`.

**"API key not set or invalid"**
```bash
attio config set api-key YOUR_KEY_HERE
# or
export ATTIO_API_KEY=YOUR_KEY_HERE
```

**Rate limit hit (429) during bulk intake**
The CLI's tenacity retry layer handles automatic retry with backoff. If retries exhaust, it will surface an error. Pause for 60 seconds and resume. For large batches (100+ contacts), add manual pauses between every 10 contacts to stay well under the 60 req/min cap.
