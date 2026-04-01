---
title: prospect-intake
type: workflow-spec
tool: n8n (or Trigger.dev)
status: draft
created: 2026-03-31
---

# Workflow: `prospect-intake`

Bulk upsert enriched Clay prospects into Attio as person + company records, dedup by email, add to outreach list, and emit a summary report.

---

## Purpose

LeadGrow's enrichment pipeline runs in Clay. When a table is ready, enriched rows need to land in Attio before outreach begins. This workflow:

1. Ingests enriched rows from Clay (via webhook, Google Sheets, or manual CSV)
2. Deduplicates against existing Attio records by email
3. Creates or updates person + company records
4. Asserts each person onto the target outreach list
5. Logs a per-row result and emits a final summary

This is the bridge between Clay enrichment and Attio CRM. Nothing goes to outreach until this has run clean.

---

## Trigger Options

### (a) Clay Webhook — Preferred

Clay fires a webhook when a table finishes enrichment.

- **Type:** Webhook (POST)
- **n8n node:** `Webhook` trigger
- **Payload format:** `{ "rows": [ {...}, {...} ] }` — array of enriched records
- **Setup in Clay:** Table Settings → Webhooks → Add webhook → `On table run complete` → point to n8n webhook URL
- **Auth:** Add a `X-Webhook-Secret` header in Clay, validate it in the first n8n node

### (b) Scheduled Google Sheets Poll

For teams that export Clay output to a Google Sheet before import.

- **Type:** Cron schedule (e.g., every 15 min or daily at 7am)
- **n8n node:** `Schedule` trigger → `Google Sheets` node (read rows where `status = "ready"`)
- **Dedup guard:** After processing, update the `status` column to `"imported"` to prevent re-processing

### (c) Manual CSV Upload

For one-off imports or testing.

- **Type:** Manual trigger with file upload
- **n8n node:** `Manual Trigger` → `Read Binary File` → `Spreadsheet File` (parse CSV)
- **Usage:** Drag enriched CSV into n8n execution, run workflow

---

## Input Data Shape

Each row represents one Clay-enriched prospect. All fields are strings unless noted.

```json
{
  "first_name": "Sarah",
  "last_name": "Chen",
  "email": "sarah.chen@storylane.io",
  "company_name": "Storylane",
  "title": "Head of Growth",
  "linkedin_url": "https://www.linkedin.com/in/sarahchen/",
  "website": "https://storylane.io",
  "phone": "+1-415-555-0192",
  "location_city": "San Francisco",
  "location_state": "CA",
  "location_country": "US",
  "company_domain": "storylane.io",
  "company_linkedin_url": "https://www.linkedin.com/company/storylane",
  "company_size": "51-200",
  "company_industry": "Software",
  "company_description": "Interactive product demo platform",
  "tech_stack": "HubSpot, Intercom, Segment",
  "persona_tag": "Head of Growth",
  "icp_score": "A",
  "enrichment_source": "Clay",
  "enriched_at": "2026-03-31T08:00:00Z"
}
```

**Required fields:** `email`, `first_name`, `last_name`, `company_name`
**Optional but valuable:** `linkedin_url`, `company_domain`, `icp_score`, `title`

---

## Steps

### Step 1 — Receive / Read Enriched Rows

**Node:** Webhook trigger (or Sheet reader, or CSV parser depending on trigger)

- Validate `X-Webhook-Secret` header if using Clay webhook trigger
- Parse payload into array of row objects
- Filter out rows missing `email` — log as `SKIPPED: no_email`, do not process
- Set batch size for downstream processing (see rate limit note)

**Output:** Array of valid prospect objects ready for processing

---

### Step 2 — For Each Row: Search Attio for Existing Person by Email

**Node:** `HTTP Request` (loop via `SplitInBatches` or `Loop Over Items`)

**Attio API call — Search people by email:**

```
POST https://api.attio.com/v2/objects/people/records/query
Authorization: Bearer {ATTIO_API_KEY}
Content-Type: application/json

{
  "filter": {
    "email_addresses": {
      "$eq": "sarah.chen@storylane.io"
    }
  },
  "limit": 1
}
```

**Response handling:**
- `data.length > 0` → person exists → capture `record_id`, route to **Step 4 (Update)**
- `data.length === 0` → person not found → route to **Step 3 (Create)**

---

### Step 3 — If Not Found: Create Person + Company Records

Run company upsert first. Person creation can reference the company record.

#### 3a — Upsert Company by Domain

```
PUT https://api.attio.com/v2/objects/companies/records
Authorization: Bearer {ATTIO_API_KEY}
Content-Type: application/json

{
  "data": {
    "values": {
      "name": [{ "value": "Storylane" }],
      "domains": [{ "domain": "storylane.io" }],
      "primary_location": [{ "locality": "San Francisco", "region": "CA", "country_code": "US" }],
      "categories": [{ "value": "Software" }],
      "description": [{ "value": "Interactive product demo platform" }],
      "linkedin": [{ "value": "https://www.linkedin.com/company/storylane" }]
    }
  },
  "matching_attribute": "domains"
}
```

Capture returned `record_id` as `company_record_id`.

#### 3b — Create Person

```
POST https://api.attio.com/v2/objects/people/records
Authorization: Bearer {ATTIO_API_KEY}
Content-Type: application/json

{
  "data": {
    "values": {
      "name": [{ "first_name": "Sarah", "last_name": "Chen" }],
      "email_addresses": [{ "email_address": "sarah.chen@storylane.io" }],
      "job_title": [{ "value": "Head of Growth" }],
      "linkedin": [{ "value": "https://www.linkedin.com/in/sarahchen/" }],
      "phone_numbers": [{ "phone_number": "+1-415-555-0192" }],
      "company": [{ "target_object": "companies", "target_record_id": "{company_record_id}" }]
    }
  }
}
```

Capture returned `record_id` as `person_record_id`. Log result as `CREATED`.

---

### Step 4 — If Found: Update with New Enrichment Data (PATCH)

```
PATCH https://api.attio.com/v2/objects/people/records/{person_record_id}
Authorization: Bearer {ATTIO_API_KEY}
Content-Type: application/json

{
  "data": {
    "values": {
      "job_title": [{ "value": "Head of Growth" }],
      "linkedin": [{ "value": "https://www.linkedin.com/in/sarahchen/" }],
      "phone_numbers": [{ "phone_number": "+1-415-555-0192" }]
    }
  }
}
```

Only patch fields that are non-null in the incoming row — do not overwrite existing Attio data with empty strings. Use an `IF` node or code node to filter out blank values before building the patch body.

Log result as `UPDATED`.

---

### Step 5 — Add to Target Outreach List

Assert the person onto the target Attio list. This is idempotent — asserting an existing entry is a no-op.

```
PUT https://api.attio.com/v2/lists/{LIST_ID}/entries
Authorization: Bearer {ATTIO_API_KEY}
Content-Type: application/json

{
  "data": {
    "record_id": {
      "object_slug": "people",
      "record_id": "{person_record_id}"
    }
  }
}
```

`LIST_ID` is the Attio list UUID. Store this as a workflow-level variable or environment variable — do not hardcode inline.

---

### Step 6 — Log Result Per Row

For each processed row, append to an in-memory results array:

```json
{
  "email": "sarah.chen@storylane.io",
  "result": "CREATED",
  "person_record_id": "abc-123",
  "company_record_id": "def-456",
  "timestamp": "2026-03-31T08:15:00Z",
  "error": null
}
```

Result values: `CREATED`, `UPDATED`, `SKIPPED`, `ERROR`

---

## Attio API Calls — Reference Summary

| Action | Method | Endpoint |
|---|---|---|
| Search person by email | POST | `/v2/objects/people/records/query` |
| Create person | POST | `/v2/objects/people/records` |
| Update person | PATCH | `/v2/objects/people/records/{record_id}` |
| Upsert company | PUT | `/v2/objects/companies/records` |
| Assert list entry | PUT | `/v2/lists/{list_id}/entries` |

Base URL: `https://api.attio.com`
Auth header: `Authorization: Bearer {ATTIO_API_KEY}`

---

## Error Handling

| Error Condition | Behavior |
|---|---|
| Missing `email` field | Skip row immediately. Log `SKIPPED: no_email`. Do not call Attio. |
| Missing `first_name` or `last_name` | Skip row. Log `SKIPPED: missing_required_field`. |
| HTTP 429 (rate limit) | Catch error → wait (see rate limit section) → retry up to 3 times → if still failing, log `ERROR: rate_limit` and continue |
| HTTP 404 on PATCH | Record was deleted between search and update. Treat as new, re-run create path. |
| HTTP 422 (validation error) | Log `ERROR: validation` with Attio's error body. Skip row. Continue processing. |
| HTTP 5xx (Attio server error) | Retry once after 5 seconds. If still failing, log `ERROR: server_error` and continue. |
| Company upsert failure | Log warning but do not block person creation. Create person without company link. |
| List assert failure | Log warning. Person record still created/updated. Flag for manual list add. |

**Core principle: partial failures do not stop the batch.** Log and continue. Every row gets processed.

---

## Rate Limit Handling

Attio v2 enforces **60 requests per minute** per API key (1 req/sec average).

At bulk scale (500+ rows), each row triggers up to 5 API calls (query + company upsert + person create/patch + list assert). Unthrottled, a 500-row batch = ~2,500 calls, which will hit the rate limit hard.

**Implementation approach:**

1. **Batch processing:** Use `SplitInBatches` node with batch size of **10 rows**
2. **Inter-batch delay:** Add a `Wait` node of **12 seconds** between batches. This targets ~50 req/min — safely under the 60/min cap with headroom for retries.
3. **Per-call retry on 429:** Catch HTTP 429 → wait 60 seconds (full window reset) → retry. Max 3 retries per call.
4. **Exponential backoff:** If retry after 60s still hits 429, wait 120s then 240s before final failure.

**Math for sizing:**

| Batch Size | Calls/Batch | Delay Between Batches | Effective Rate |
|---|---|---|---|
| 10 rows | ~50 calls | 12s | ~50 req/min |
| 5 rows | ~25 calls | 6s | ~50 req/min |

For runs over 1,000 rows, consider splitting into multiple workflow executions across a longer time window (e.g., 250 rows/run, 4 runs over 2 hours).

---

## Output — Summary Report

After all rows are processed, emit a summary. In n8n, use a `Code` node to aggregate the results array:

```json
{
  "run_id": "prospect-intake-2026-03-31-0815",
  "triggered_at": "2026-03-31T08:00:00Z",
  "completed_at": "2026-03-31T09:12:00Z",
  "total_rows": 312,
  "created": 198,
  "updated": 87,
  "skipped": 21,
  "errors": 6,
  "error_rows": [
    { "email": "bad@example.com", "error": "validation", "detail": "invalid phone format" }
  ],
  "list_id": "{LIST_ID}",
  "list_entries_asserted": 285
}
```

**Delivery options:**
- Write to Google Sheets summary tab (`Google Sheets` node)
- Post to Slack `#clay-pipeline` channel with formatted message
- Save to `clients/gtm-client-[name]/reports/intake-YYYY-MM-DD.json`
- All three — run in parallel as the final step

---

## Environment Variables

Store these outside workflow config — never hardcode in node parameters:

| Variable | Description |
|---|---|
| `ATTIO_API_KEY` | Attio v2 bearer token |
| `ATTIO_LIST_ID` | Target outreach list UUID |
| `CLAY_WEBHOOK_SECRET` | Shared secret for webhook validation |
| `GOOGLE_SHEETS_ID` | Sheet ID for CSV poll trigger (if using trigger b) |

In n8n: Settings → Variables. In Trigger.dev: project environment variables.

---

## Notes for the Developer

- **Attio list IDs** are UUIDs, not slugs. Get them via `GET /v2/lists` and store the ID, not the display name.
- **Company matching** uses `domains` as the `matching_attribute` on the PUT upsert. If no domain is present, fall back to `name` — but expect false positives. Prefer domain.
- **Attio attribute slugs** (`job_title`, `linkedin`, etc.) must match the exact attribute API slug in your Attio workspace. If using custom attributes, pull the slug from Attio's attribute settings page.
- **n8n vs Trigger.dev:** This spec is tool-agnostic. In Trigger.dev, `SplitInBatches` + `Wait` translates to `for await` with `await setTimeout` or `io.wait`. The HTTP calls and logic are identical.
- **Idempotency:** Running this workflow twice on the same input is safe. Person search → create/update, company PUT with `matching_attribute`, and list assert PUT are all idempotent by design.
