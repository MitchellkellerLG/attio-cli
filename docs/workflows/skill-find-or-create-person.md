---
name: find-or-create-person
description: Resolve a person in Attio by email or name. Searches first, creates only if not found. Returns record_id. Use before any workflow that needs to write to a person record — notes, tasks, list entries, deals.
triggers:
  - resolve person by email
  - get or create contact
  - find person in attio
  - ensure person exists
  - before adding note to person
  - before assigning to list
---

# Skill: find-or-create-person

## Purpose

Every Attio write operation (notes, tasks, list entries, attribute updates) requires a `record_id`. This skill is the resolution layer that produces one — reliably, without duplicates.

It searches Attio for a person by email (preferred) or name, returns the existing record if found, and creates a new one only when no match exists. It always returns a `record_id` the calling workflow can act on immediately.

**Why it's foundational:** Without a resolved `record_id`, no downstream Attio operation can proceed. Building this resolution step into every individual workflow creates duplication and inconsistency. This skill centralizes the logic once, and every other skill calls it.

---

## Trigger

Invoke this skill whenever a workflow needs to operate on a person record and the `record_id` is not already known. Specifically:

- Before adding a note to a person
- Before assigning a person to a list or updating list entry status
- Before creating or linking a task to a person
- Before writing any attribute (title, company, phone, custom fields)
- During data ingestion when processing lead lists or enriched contacts
- Any time you have an email address and need to act on the corresponding record

Do **not** invoke this if you already have a `record_id` from a previous step in the same session.

---

## Inputs

| Input | Required | Notes |
|---|---|---|
| `email` | Yes (strongly preferred) | Primary matching key. Attio treats email as a unique identifier. Exact match only — fuzzy search by email is unreliable. |
| `name` | Optional | Used as fallback if no email, or to populate the `name` field on create. Format: `"First Last"`. |
| `object` | Optional | Defaults to `people`. Pass `companies` if resolving a company record instead. |

**Rules:**
- If `email` is available, always use it — never skip it in favor of name-only search.
- If only `name` is available, treat any match as a candidate and apply the ambiguity logic (see Error Handling).
- If both are available, search by email first. Use name only to populate the created record.

---

## Steps

### Step 1 — Search by email (primary path)

Use the `list` command with a filter on `email_addresses` to perform an exact-match query. This is more reliable than `search` for email resolution because `search` is fuzzy and may return partial matches.

```bash
attio people list \
  --filter 'email_addresses=jane.doe@acme.com' \
  --limit 5 \
  --json
```

**Parse the response:**
- `data` array length = 0 → person does not exist. Proceed to Step 3.
- `data` array length = 1 → person found. Extract `id.record_id`. Skip to Output.
- `data` array length > 1 → multiple records share this email. Apply ambiguity logic (see Error Handling).

---

### Step 2 — Fallback search by name (only if no email)

If no email is available, use the fuzzy `search` command:

```bash
attio people search "Jane Doe" --limit 5 --json
```

**Parse the response:**
- `hits` array length = 0 → person does not exist. Proceed to Step 3.
- `hits` array length = 1 → likely match. Verify name similarity before accepting. If confident, extract `record.id.record_id`. Skip to Output.
- `hits` array length > 1 → ambiguous. Apply ambiguity logic (see Error Handling).

---

### Step 3 — Create the record (only if not found)

If no match was found in Steps 1 or 2, create a new person record.

**With email and name:**
```bash
attio people create \
  --values '{"email_addresses": [{"email_address": "jane.doe@acme.com"}], "name": [{"first_name": "Jane", "last_name": "Doe"}]}' \
  --json
```

**With email only (name unknown):**
```bash
attio people create \
  --values '{"email_addresses": [{"email_address": "jane.doe@acme.com"}]}' \
  --json
```

**With name only (no email — use sparingly):**
```bash
attio people create \
  --values '{"name": [{"first_name": "Jane", "last_name": "Doe"}]}' \
  --json
```

Extract `data.id.record_id` from the response.

---

### Alternative: Assert (upsert) path

If the calling workflow only needs to ensure a record exists and does not need to branch on created-vs-found, use `assert` instead of the search-then-create pattern. Assert performs the upsert in a single API call:

```bash
attio people assert \
  --matching-attribute email_addresses \
  --values '{"email_addresses": [{"email_address": "jane.doe@acme.com"}], "name": [{"first_name": "Jane", "last_name": "Doe"}]}' \
  --json
```

**When to use assert vs search-then-create:**
- Use `assert` when you don't care about the created/found distinction and just need a `record_id`.
- Use search-then-create when the calling workflow needs to know whether the record was new (e.g., to trigger a welcome sequence only for new contacts, or to avoid overwriting existing data).

---

## Output

Always return a structured result to the calling workflow:

```json
{
  "record_id": "abc123de-f456-7890-abcd-ef1234567890",
  "status": "found",
  "object": "people"
}
```

Or for a newly created record:

```json
{
  "record_id": "abc123de-f456-7890-abcd-ef1234567890",
  "status": "created",
  "object": "people"
}
```

| Field | Type | Description |
|---|---|---|
| `record_id` | string (UUID) | The Attio record ID. Pass this to all downstream operations. |
| `status` | `"found"` \| `"created"` | Whether the record already existed or was just created. |
| `object` | `"people"` \| `"companies"` | Object type operated on (mirrors the `object` input). |

The `record_id` in the Attio API response lives at `data.id.record_id` (for single-record responses) or `data[0].id.record_id` (for list responses).

---

## Error Handling

### Multiple results for the same email

If Step 1 returns more than one record matching an email address, this indicates a data integrity issue in the Attio workspace (duplicate records).

**Do not arbitrarily pick one.** Instead:

1. Log all matching `record_id` values.
2. Return an error to the calling workflow:
   ```json
   {
     "error": "ambiguous_match",
     "message": "Found 2 records matching email jane.doe@acme.com",
     "candidates": ["record_id_1", "record_id_2"],
     "object": "people"
   }
   ```
3. The calling workflow should surface this to a human for deduplication. Do not proceed with writes until resolved.

### Multiple results for a name-only search

Name search is inherently ambiguous. If `search` returns more than one result with no email to disambiguate:

1. Check if any candidate has a matching company name or title (if those were provided as inputs).
2. If a single candidate matches on multiple signals, use it and note the confidence was indirect.
3. If still ambiguous, return an error with `candidates` array (same shape as above).
4. Never create a new record when a plausible name match exists — you will create a duplicate.

### Create fails (409 Conflict)

Attio may return a 409 if a record with the same email already exists and you attempted a plain `create` (not `assert`). This can happen due to a race condition between Steps 1 and 3.

On 409: retry Step 1 immediately to fetch the now-existing record. Do not retry the create.

### Network / auth errors

These are handled by the CLI's built-in retry logic (3 attempts, exponential backoff for 429/5xx, immediate fail on 401). Surface the CLI's error output directly to the calling workflow. Do not swallow auth errors.

---

## Example Usage

### Example 1 — Inbound lead from a form fill

A new lead submits a form with email and full name. Resolve before adding to the "Inbound Leads" list.

```bash
# Step 1: Search by email
attio people list \
  --filter 'email_addresses=tom.chen@quantumleap.io' \
  --limit 5 \
  --json

# Response: data is empty → not found

# Step 3: Create
attio people create \
  --values '{"email_addresses": [{"email_address": "tom.chen@quantumleap.io"}], "name": [{"first_name": "Tom", "last_name": "Chen"}]}' \
  --json

# Response includes: data.id.record_id = "d91f3a2b-..."
# Output: { "record_id": "d91f3a2b-...", "status": "created", "object": "people" }

# Downstream: add to list
attio entries create <list_id> --record-id "d91f3a2b-..." --json
```

---

### Example 2 — Meeting follow-up, person already in CRM

After a discovery call, log a note to the prospect's record.

```bash
# Step 1: Search by email
attio people list \
  --filter 'email_addresses=sarah.okonkwo@meridianops.com' \
  --limit 5 \
  --json

# Response: data has 1 result → found
# record_id = "7bc82e10-..."
# Output: { "record_id": "7bc82e10-...", "status": "found", "object": "people" }

# Downstream: create note
attio notes create \
  --parent-object people \
  --parent-record-id "7bc82e10-..." \
  --title "Discovery call 2026-03-31" \
  --content "Pain: manual reporting. Budget: confirmed. Next: send proposal." \
  --json
```

---

### Example 3 — Upsert path for bulk enrichment (assert)

Processing a CSV of 200 enriched contacts. Don't need the created/found distinction — just need every contact to exist in Attio with current data.

```bash
# Single assert call per contact — one API round trip, no search step needed
attio people assert \
  --matching-attribute email_addresses \
  --values '{"email_addresses": [{"email_address": "marcus.riley@vertexdata.co"}], "name": [{"first_name": "Marcus", "last_name": "Riley"}], "job_title": [{"value": "VP of Revenue Operations"}]}' \
  --json

# Response includes record_id regardless of whether it was created or updated
# Output: { "record_id": "2fe91c44-...", "status": "found", "object": "people" }
```

---

## CLI Commands Used

| Command | Purpose |
|---|---|
| `attio people list --filter --json` | Exact-match search by email (primary resolution path) |
| `attio people search <query> --json` | Fuzzy search by name (fallback when no email) |
| `attio people create --values --json` | Create a new person record |
| `attio people assert --matching-attribute --values --json` | Upsert — create or update in one call (alternative path) |
| `attio companies list --filter --json` | Same resolution pattern for company records |
| `attio companies assert --matching-attribute --values --json` | Upsert for companies |
