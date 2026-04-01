# n8n Workflow: `attio-to-clay`

**Version:** 1.0
**Last updated:** 2026-03-31
**Owner:** LeadGrow / attio-cli project
**Direction:** Attio list → Clay table (reverse of prospect-intake)

---

## Purpose

Export entries from an Attio list into a Clay table via webhook for re-enrichment or campaign targeting. Use this when a list of contacts already exists in Attio and needs to flow back into Clay — for a new outbound campaign push, a re-enrichment pass, or a targeted drip.

This is the reverse of `prospect-intake` (Clay → Attio). No new records are created in Attio; this workflow reads and ships.

---

## Trigger Options

### (a) Manual Trigger — On-demand export

- Node type: `n8n-nodes-base.manualTrigger` or `n8n-nodes-base.formTrigger`
- Inputs collected at trigger time:
  - `attio_list_id` (string, required) — the Attio list to pull from
  - `clay_webhook_url` (string, required) — target Clay table webhook URL
  - `field_mapping` (JSON, optional) — override default field mapping (see Inputs)

Use this for ad-hoc exports. Recommended default.

### (b) Webhook Trigger — Fire when list reaches N entries

- Node type: `n8n-nodes-base.webhook`
- Attio sends a webhook event when list membership changes
- Workflow checks current list count; proceeds if `entry_count >= threshold`
- Config:
  - `threshold` (integer) — minimum list size to trigger export (e.g., 50)
  - `attio_list_id` extracted from webhook payload
  - `clay_webhook_url` stored as n8n credential or env variable

> Note: Attio webhook events for list changes must be configured in Attio's developer settings. Event type: `list-entry.created` or `list-entry.updated`.

---

## Inputs

| Input | Type | Required | Default | Description |
|---|---|---|---|---|
| `attio_list_id` | string | Yes | — | Attio list UUID to pull entries from |
| `clay_webhook_url` | string | Yes | — | Clay table webhook URL (POST target) |
| `field_mapping` | JSON object | No | See below | Map Attio field slugs to Clay column names |
| `batch_size` | integer | No | 100 | Records per Attio API page |
| `retry_attempts` | integer | No | 3 | Max retries per failed Clay POST |

### Default Field Mapping

```json
{
  "email_addresses[0].email_address": "email",
  "first_name": "first_name",
  "last_name": "last_name",
  "company.name": "company",
  "job_title": "title",
  "linkedin_profile_url": "linkedin_url"
}
```

Override via `field_mapping` input at trigger time to add or rename columns.

---

## Steps

### Step 1 — Pull list entries from Attio (with person record expansion)

Fetch all entries in the given Attio list. Use pagination (`limit` / `offset`) to handle lists of any size.

**Node type:** `n8n-nodes-base.httpRequest` (loop with `SplitInBatches` for pagination)

```
POST https://api.attio.com/v2/lists/{list_id}/entries/query
Authorization: Bearer {{$credentials.attioApiKey}}
Content-Type: application/json

{
  "expand": ["record_reference"],
  "limit": 100,
  "offset": 0
}
```

- Expand `record_reference` to get the full person record (name, email, title, LinkedIn) inline — avoids N+1 lookups.
- Loop until `has_more: false` or response count < `limit`.
- Collect all entries into a single array before proceeding.

> See [Attio API Calls](#attio-api-calls) section for full endpoint details.

---

### Step 2 — Extract relevant fields

Transform each raw Attio entry into a flat Clay-ready row.

**Node type:** `n8n-nodes-base.code` (JavaScript)

```javascript
const mapping = $input.first().json.field_mapping || DEFAULT_MAPPING;

return items.map(item => {
  const record = item.json.record_reference;  // expanded person record
  const row = {};

  for (const [attioDotPath, clayColumn] of Object.entries(mapping)) {
    row[clayColumn] = resolveDotPath(record, attioDotPath) ?? null;
  }

  // Tag the source for Clay tracking
  row._source = "attio-export";
  row._attio_record_id = record.record_id;
  row._exported_at = new Date().toISOString();

  return { json: row };
});
```

**After extraction, filter:**

- Skip rows where `email` is null or empty (log as skipped, not failed).
- Normalize email to lowercase.

---

### Step 3 — POST each row to Clay table webhook

Send one HTTP POST per row to the Clay table webhook URL.

**Node type:** `n8n-nodes-base.httpRequest`

- Method: `POST`
- URL: `{{$json.clay_webhook_url}}` (from trigger input)
- Body: JSON row from Step 2
- Headers: `Content-Type: application/json`
- On error: retry up to `retry_attempts` times with 2-second exponential backoff
- Timeout: 10 seconds per request

> See [Clay Integration](#clay-integration) for webhook behavior details.

Track per-row outcomes:
- `sent` — 2xx response received
- `failed` — all retries exhausted, non-2xx response
- `skipped` — no email address present

---

### Step 4 — Log sent/failed/skipped counts

Aggregate results and write a summary log.

**Node type:** `n8n-nodes-base.code` + optional `n8n-nodes-base.httpRequest` (POST to Slack/webhook for notifications)

```javascript
const results = $input.all();
const sent    = results.filter(r => r.json.status === "sent").length;
const failed  = results.filter(r => r.json.status === "failed").length;
const skipped = results.filter(r => r.json.status === "skipped").length;

const summary = {
  workflow: "attio-to-clay",
  attio_list_id: $env.ATTIO_LIST_ID,
  clay_webhook_url: $env.CLAY_WEBHOOK_URL,
  timestamp: new Date().toISOString(),
  total: results.length,
  sent,
  failed,
  skipped,
  failed_records: results
    .filter(r => r.json.status === "failed")
    .map(r => ({ email: r.json.email, error: r.json.error }))
};

console.log(JSON.stringify(summary, null, 2));
return [{ json: summary }];
```

If `failed > 0`, the workflow should emit a non-success status and optionally post a Slack notification with the failed record list.

---

## Attio API Calls

### List entries with record expansion

```
POST https://api.attio.com/v2/lists/{list_id}/entries/query
Authorization: Bearer {ATTIO_API_KEY}
Content-Type: application/json
```

**Request body:**

```json
{
  "expand": ["record_reference"],
  "limit": 100,
  "offset": 0
}
```

**Response shape (abbreviated):**

```json
{
  "data": [
    {
      "id": { "entry_id": "abc123" },
      "record_reference": {
        "record_id": "person_xyz",
        "object_slug": "people",
        "values": {
          "email_addresses": [{ "email_address": "jane@acme.com" }],
          "first_name": [{ "value": "Jane" }],
          "last_name": [{ "value": "Smith" }],
          "job_title": [{ "value": "VP of Sales" }],
          "linkedin_profile_url": [{ "value": "https://linkedin.com/in/janesmith" }],
          "company": [{ "target_record": { "record_id": "company_abc", "values": { "name": [{ "value": "Acme Corp" }] } } }]
        }
      }
    }
  ],
  "has_more": true
}
```

**Pagination:** Increment `offset` by `limit` on each page until `has_more: false`.

**Auth:** Store API key as an n8n credential (`attioApiKey`). Never hardcode.

**Rate limits:** Attio allows 60 requests/minute on standard plans. For lists > 6,000 entries, add a 1-second delay between page fetches.

---

## Clay Integration

Clay tables accept inbound data via **table webhooks** — a unique POST endpoint per table.

### How it works

1. In Clay: open the target table → Integrations → Webhook → copy the webhook URL.
2. POST a JSON object to that URL. Each POST creates one row in the table.
3. Clay maps JSON keys to columns automatically if column names match, or via Clay's field mapper UI.
4. Clay responds with `200 OK` on success. Any non-2xx means the row was rejected.

### Example POST

```
POST https://hook.clay.com/tables/{table_id}/rows
Content-Type: application/json

{
  "email": "jane@acme.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "company": "Acme Corp",
  "title": "VP of Sales",
  "linkedin_url": "https://linkedin.com/in/janesmith",
  "_source": "attio-export",
  "_attio_record_id": "person_xyz",
  "_exported_at": "2026-03-31T10:00:00Z"
}
```

### Column naming

Clay column names are case-sensitive and must match the JSON keys exactly. The `_source`, `_attio_record_id`, and `_exported_at` metadata fields will be created as new columns on first run — this is expected behavior.

---

## Error Handling

### Missing email (skip, don't fail)

- After field extraction (Step 2), check `row.email` is non-null and non-empty.
- If missing: set `status: "skipped"`, log the `_attio_record_id`, and exclude from Clay POST queue.
- Skipped records are reported in the summary but do not count as failures.

### Clay webhook failure (retry + log)

- On non-2xx response from Clay: wait 2 seconds, retry up to `retry_attempts` (default 3).
- If all retries fail: mark `status: "failed"`, capture `{ email, error_code, error_body }`.
- Do not throw — continue processing remaining records.
- All failed records are collected and included in the Step 4 summary log.
- If `failed > 0` at end of run: workflow exits with a warning status, not success.

### Attio API failure

- If Attio returns a non-2xx on any page fetch: throw immediately and halt the workflow.
- Log the page `offset` that failed so the run can be resumed manually from that point.
- Do not send partial data to Clay without logging that the Attio pull was incomplete.

### Empty list

- If the list has 0 entries, log `"List is empty, nothing to export"` and exit cleanly (no error).

---

## Output

On completion, the workflow produces a JSON summary:

```json
{
  "workflow": "attio-to-clay",
  "attio_list_id": "list_abc123",
  "clay_webhook_url": "https://hook.clay.com/tables/xyz/rows",
  "timestamp": "2026-03-31T10:05:32Z",
  "total": 142,
  "sent": 138,
  "failed": 2,
  "skipped": 2,
  "failed_records": [
    { "email": "bad@domain.com", "error": "422 Unprocessable Entity" },
    { "email": "test@test.com", "error": "timeout after 3 retries" }
  ]
}
```

**Success state:** `failed === 0`
**Partial success:** `failed > 0` — review `failed_records` and re-run those rows manually or via filtered re-export
**Hard failure:** Attio pull error or workflow crash — check n8n execution logs for the faulting step

---

## Environment Variables / Credentials

| Variable | Where | Description |
|---|---|---|
| `ATTIO_API_KEY` | n8n credential | Attio API key (Bearer token) |
| `CLAY_WEBHOOK_URL` | Trigger input or n8n env | Target Clay table webhook URL |
| `ATTIO_LIST_ID` | Trigger input | List to export |

Store secrets in n8n's credential store. Never pass as plain query params.

---

## Related Workflows

- `prospect-intake` — opposite direction: Clay → Attio (creates new person records)
- `attio-list-refresh` — re-enriches existing Attio list records in place (no Clay involved)
