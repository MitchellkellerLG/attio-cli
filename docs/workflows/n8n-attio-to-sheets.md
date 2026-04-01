---
title: n8n Workflow — attio-to-sheets
type: developer-handoff-spec
status: ready-to-build
created: 2026-03-31
---

# n8n Workflow: `attio-to-sheets`

Weekly export of Attio CRM data (pipeline, tasks, lists) into Google Sheets for LeadGrow client reporting.

---

## Purpose

LeadGrow runs weekly client reporting cycles. This workflow pulls live data from Attio and writes it into a shared Google Sheet, replacing the manual export process. Three tabs cover pipeline health, open task status, and list membership counts. The sheet is the single source of truth handed to clients and internal reviewers each Monday.

---

## Trigger

| Type     | Config                            |
| -------- | --------------------------------- |
| Schedule | Monday 8:00am (workspace timezone) |
| Manual   | Via n8n "Execute workflow" button  |

**n8n node:** `Schedule Trigger`
Cron expression: `0 8 * * 1`

---

## What Gets Exported

| Tab | Name | Contents |
| --- | ---- | -------- |
| 1 | `Pipeline` | People + companies, deal stage, owner, last activity |
| 2 | `Open Tasks` | All non-completed tasks, deadlines, assignees, linked record |
| 3 | `Lists` | All active lists with entry counts and last modified date |

---

## Workflow Steps

### Step 1 — Pull Data from Attio API

Three parallel HTTP request nodes, one per data type. Run them in parallel (connect all three to the trigger, then merge downstream).

#### 1a. People / Pipeline

```
GET https://api.attio.com/v2/objects/people/records/query
```

**Body:**
```json
{
  "limit": 500,
  "offset": 0,
  "sorts": [
    { "attribute": "last_interaction_at", "direction": "desc" }
  ],
  "attributes": [
    "name",
    "email_addresses",
    "company",
    "job_title",
    "status",
    "owner",
    "created_at",
    "last_interaction_at"
  ]
}
```

Paginate if `response.data.length === 500`. Add a loop node that increments `offset` by 500 until results < 500.

#### 1b. Open Tasks

```
GET https://api.attio.com/v2/tasks
```

**Query params:**
```
?status=open
&limit=500
&sort=deadline_at
&sort_direction=asc
```

Attio returns tasks with `linked_records` arrays. Each task object includes `assignees`, `deadline_at`, `content`, `created_at`, and `record_references`.

#### 1c. Lists

```
GET https://api.attio.com/v2/lists
```

No params needed. Returns all workspace lists. For each list, pull entry count:

```
GET https://api.attio.com/v2/lists/{list_id}/entries/query
```

**Body:**
```json
{ "limit": 1 }
```

Read `response.total` from the response (not `data.length`). Run this as a sub-loop over each list from the first call.

**Auth for all calls:**
```
Authorization: Bearer {{$env.ATTIO_API_KEY}}
Content-Type: application/json
```

---

### Step 2 — Transform JSON to Flat Rows

Use `Code` nodes (JavaScript) immediately after each HTTP node.

#### 2a. Transform People / Pipeline

```javascript
const records = $input.first().json.data;

return records.map(r => {
  const vals = r.values;
  return {
    name: vals.name?.[0]?.full_name ?? '',
    email: vals.email_addresses?.[0]?.email_address ?? '',
    company: vals.company?.[0]?.target_record_id ?? '',
    job_title: vals.job_title?.[0]?.value ?? '',
    status: vals.status?.[0]?.status?.title ?? '',
    owner: vals.owner?.[0]?.referenced_actor?.name ?? '',
    created_at: vals.created_at?.[0]?.value ?? '',
    last_interaction_at: vals.last_interaction_at?.[0]?.value ?? '',
  };
});
```

#### 2b. Transform Open Tasks

```javascript
const tasks = $input.first().json.data;

return tasks.map(t => {
  const linkedRecord = t.linked_records?.[0];
  return {
    task_id: t.id?.task_id ?? '',
    content: t.content ?? '',
    status: t.is_completed ? 'Completed' : 'Open',
    deadline: t.deadline_at ?? '',
    assignee: t.assignees?.[0]?.referenced_actor?.name ?? '',
    linked_record_type: linkedRecord?.target_object ?? '',
    linked_record_id: linkedRecord?.target_record_id ?? '',
    created_at: t.created_at ?? '',
  };
});
```

#### 2c. Transform Lists

```javascript
// $input.all() contains one item per list, each with list metadata + entry_count injected
const lists = $input.all();

return lists.map(item => {
  const l = item.json;
  return {
    list_id: l.id?.list_id ?? '',
    name: l.name ?? '',
    object_type: l.parent_object ?? '',
    entry_count: l.entry_count ?? 0,
    created_at: l.created_at ?? '',
    workspace_member_count: l.workspace_member_count ?? '',
  };
});
```

---

### Step 3 — Write to Google Sheets

Use the **Google Sheets node** (OAuth2 credential) for each tab. Operation: `Clear and Append` (not plain append — always full rewrite to avoid stale rows).

**Sequence per tab:**
1. `Clear Range` — wipe the data range (leave row 1 headers intact)
2. `Append` — write transformed rows starting at row 2

Or use the single `Clear and Append` operation if available in your n8n Google Sheets node version — it handles both in one call.

**Credential:** Google OAuth2 with Sheets + Drive scopes (`https://www.googleapis.com/auth/spreadsheets`).

---

## Google Sheets Setup

**Sheet name:** `LeadGrow — Attio Weekly Export`
Create this sheet manually once, share with the service account or OAuth user n8n authenticates as.

### Tab 1: `Pipeline`

| Column | Header | Source Field |
| ------ | ------ | ------------ |
| A | Name | `name` |
| B | Email | `email` |
| C | Company ID | `company` |
| D | Job Title | `job_title` |
| E | Status | `status` |
| F | Owner | `owner` |
| G | Created At | `created_at` |
| H | Last Interaction | `last_interaction_at` |

Clear range: `Pipeline!A2:H`

### Tab 2: `Open Tasks`

| Column | Header | Source Field |
| ------ | ------ | ------------ |
| A | Task ID | `task_id` |
| B | Content | `content` |
| C | Status | `status` |
| D | Deadline | `deadline` |
| E | Assignee | `assignee` |
| F | Linked Record Type | `linked_record_type` |
| G | Linked Record ID | `linked_record_id` |
| H | Created At | `created_at` |

Clear range: `Open Tasks!A2:H`

### Tab 3: `Lists`

| Column | Header | Source Field |
| ------ | ------ | ------------ |
| A | List ID | `list_id` |
| B | List Name | `name` |
| C | Object Type | `object_type` |
| D | Entry Count | `entry_count` |
| E | Created At | `created_at` |

Clear range: `Lists!A2:E`

**Row 1 of each tab is frozen headers** — never cleared. Set this once in Sheets manually.

---

## Attio API Reference

| Data | Method | Endpoint |
| ---- | ------ | -------- |
| People records | `POST` | `https://api.attio.com/v2/objects/people/records/query` |
| Open tasks | `GET` | `https://api.attio.com/v2/tasks?status=open&limit=500` |
| All lists | `GET` | `https://api.attio.com/v2/lists` |
| List entry count | `POST` | `https://api.attio.com/v2/lists/{list_id}/entries/query` |

**Base URL:** `https://api.attio.com/v2`
**Auth:** Bearer token. Store as n8n credential `ATTIO_API_KEY` (environment variable) or use n8n's built-in credential store.
**Rate limit:** Attio allows 60 requests/minute on standard plans. The Lists sub-loop can hit this if you have 60+ lists. Add a 1-second Wait node between list entry count calls if needed.

---

## Error Handling

### Empty Results

After each transform node, add an `IF` node:

```
Condition: {{ $json.length }} > 0
True → proceed to Sheets write
False → send Slack/email alert: "attio-to-sheets: [Tab] returned 0 records. Skipping write."
```

Do not write to Sheets on empty results. An empty rewrite would wipe last week's data.

### Sheets API Quota

Google Sheets API allows 100 requests per 100 seconds per user. Three tabs = 6 calls (3 clears + 3 appends) — well within quota for this workflow. If you later add more tabs, add 1-second Wait nodes between writes.

On `429` from Google: n8n's Google Sheets node retries automatically with backoff. No custom handling needed unless you're seeing consistent failures — in that case, add an explicit `Wait` (2s) node before each Sheets write.

### Stale Data Warning

Add a final `Code` node that checks `last_interaction_at` across Pipeline rows:

```javascript
const rows = $input.all();
const now = Date.now();
const staleThreshold = 7 * 24 * 60 * 60 * 1000; // 7 days

const stale = rows.filter(r => {
  const last = new Date(r.json.last_interaction_at).getTime();
  return (now - last) > staleThreshold;
});

return [{ json: { stale_count: stale.length, total: rows.length } }];
```

If `stale_count / total > 0.5`, fire a Slack message: "Warning: >50% of pipeline records haven't been touched in 7+ days. Review Attio data quality."

### API Auth Failure

If any HTTP node returns `401`, n8n will stop the chain. Add an error workflow (n8n Settings > Error Workflow) that sends an alert. Don't silently swallow auth failures.

---

## Output

On successful completion, the workflow sends a Slack notification (or email — configure per team preference):

```
attio-to-sheets complete.
Pipeline: {N} records
Open Tasks: {N} tasks
Lists: {N} lists ({total entries} total entries)

Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}
Run time: {duration}ms
```

Use a `Set` node before the notification to aggregate counts from all three transform outputs, then pass them into the message template.

Store the Sheet URL as an n8n workflow variable or hardcode it once the sheet is created.

---

## Environment Variables Required

| Variable | Description |
| -------- | ----------- |
| `ATTIO_API_KEY` | Attio workspace API key (Settings > API) |
| `GOOGLE_SHEET_ID` | ID from the Sheet URL (`/d/{ID}/edit`) |
| `SLACK_WEBHOOK_URL` | For success/error notifications |

---

## Notes for the Developer

- Test the People query first — it's the most complex transform. Run a single POST with `limit: 10` and inspect the raw response before writing the transform.
- The `values` structure in Attio responses is an object of arrays (each attribute is an array of value objects). Always use `?.[0]?.value` or the appropriate field accessor — attributes are never simple strings.
- Attio's task `linked_records` array can be empty for tasks not attached to a record. The transform handles this with optional chaining — make sure it's not stripped by your n8n version.
- For the Lists entry count loop, use n8n's `Loop Over Items` node fed by the lists array. Inject `entry_count` into each list item before the final transform.
- The `gws` CLI is available in the LeadGrow workspace for one-off Sheets operations from the terminal, but the n8n workflow should use the Google Sheets node directly (OAuth2) — not shell-out to `gws`.
