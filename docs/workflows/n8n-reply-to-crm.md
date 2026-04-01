---
name: n8n-reply-to-crm
description: Developer handoff spec for the reply-to-crm n8n workflow. Auto-syncs interested replies from EmailBison to Attio — creates person record, logs reply as note, adds to Interested list, creates follow-up task.
priority: P0
status: ready-to-build
last-updated: 2026-03-31
---

# n8n Workflow: `reply-to-crm`

**Priority: P0 — Pipeline leakage prevention.** Every "Interested" reply that doesn't land in Attio is a deal that falls through the cracks.

---

## Purpose

When a prospect replies to a cold email and is marked **Interested** in EmailBison, automatically:

1. Create or update their person record in Attio
2. Log the reply text as a note with campaign context
3. Add them to the **Interested** list in Attio
4. Create a follow-up task assigned to Mitch

This workflow is the connective tissue between outbound (EmailBison) and pipeline (Attio). It runs without human intervention so no reply gets missed between the time it comes in and the time Mitch reviews it.

---

## Trigger

**Source:** EmailBison webhook
**Event:** `reply.marked_interested`

To register the webhook in EmailBison, set the webhook URL to your n8n instance's webhook path for this workflow. The event fires when a reply is manually or automatically marked Interested from the EmailBison inbox.

---

## Webhook Payload

EmailBison sends a POST request with the following JSON body:

```json
{
  "event": "reply.marked_interested",
  "timestamp": "2026-03-31T14:22:00Z",
  "data": {
    "reply_id": "rep_abc123",
    "prospect": {
      "email": "jane.doe@acme.com",
      "first_name": "Jane",
      "last_name": "Doe",
      "company": "Acme Corp",
      "title": "VP of Sales"
    },
    "reply": {
      "body": "Hey, this actually looks relevant. Can we chat next week?",
      "received_at": "2026-03-31T14:18:00Z",
      "subject": "Re: Outbound for Acme"
    },
    "campaign": {
      "id": "camp_xyz789",
      "name": "Acme — VP Sales — March 2026",
      "step_number": 2
    },
    "sender_email": "mitch@leadgrow.ai"
  }
}
```

**Note:** `first_name`, `last_name`, `title`, and `company` may be absent for contacts that weren't fully enriched. The workflow must handle missing fields gracefully — `email` is the only guaranteed field.

---

## n8n Node Sequence

### Node 1 — Webhook Receiver

**Type:** Webhook (n8n built-in)
**Method:** POST
**Path:** `/reply-to-crm`
**Authentication:** Header Auth — require `X-Webhook-Secret` header matching a stored credential

**Output mapping (set these as variables for downstream nodes):**

```
prospect_email    = {{ $json.data.prospect.email }}
prospect_name     = {{ $json.data.prospect.first_name }} {{ $json.data.prospect.last_name }}
prospect_company  = {{ $json.data.prospect.company }}
prospect_title    = {{ $json.data.prospect.title }}
reply_body        = {{ $json.data.reply.body }}
reply_received_at = {{ $json.data.reply.received_at }}
campaign_name     = {{ $json.data.campaign.name }}
campaign_id       = {{ $json.data.campaign.id }}
reply_id          = {{ $json.data.reply_id }}
```

**Pre-flight check:** Add an IF node immediately after. If `prospect_email` is empty or null, route to the error handler (Node 6). Do not proceed without an email address.

---

### Node 2 — Find or Create Person in Attio

**Type:** HTTP Request

**Step 2a — Search for existing person**

```
Method: GET
URL: https://api.attio.com/v2/objects/people/records
Headers:
  Authorization: Bearer {{ $credentials.AttioApiKey }}
  Content-Type: application/json

Query params:
  filter[email_addresses][email_address][eq]: {{ $json.prospect_email }}
```

**Step 2b — Branch on result**

Add an IF node:
- If `data.length > 0` → person exists, extract `record_id` from `data[0].id.record_id`, skip to Node 3
- If `data.length === 0` → person does not exist, proceed to create

**Step 2c — Create person (only if not found)**

```
Method: POST
URL: https://api.attio.com/v2/objects/people/records

Body (JSON):
{
  "data": {
    "values": {
      "email_addresses": [
        { "email_address": "{{ $json.prospect_email }}" }
      ],
      "name": [
        {
          "first_name": "{{ $json.prospect_first_name || '' }}",
          "last_name": "{{ $json.prospect_last_name || '' }}"
        }
      ],
      "job_title": [
        { "value": "{{ $json.prospect_title || '' }}" }
      ],
      "company": [
        { "target_object": "companies", "target_record_id": null }
      ]
    }
  }
}
```

**Note on company:** Attio links people to company records by record ID, not by name. If you want company linkage, run a separate company find-or-create step before this one. For MVP, omit the company field if no company record ID is available — don't block person creation on it.

**Output:** Store `record_id` from the response (`data.id.record_id`) for use in Nodes 3, 4, and 5.

---

### Node 3 — Create Note with Reply Text

**Type:** HTTP Request

```
Method: POST
URL: https://api.attio.com/v2/notes

Headers:
  Authorization: Bearer {{ $credentials.AttioApiKey }}
  Content-Type: application/json

Body (JSON):
{
  "data": {
    "parent_object": "people",
    "parent_record_id": "{{ $json.person_record_id }}",
    "title": "Interested reply — {{ $json.campaign_name }}",
    "content": "**Campaign:** {{ $json.campaign_name }}\n**Received:** {{ $json.reply_received_at }}\n**EmailBison Reply ID:** {{ $json.reply_id }}\n\n---\n\n{{ $json.reply_body }}",
    "created_at": "{{ $json.reply_received_at }}"
  }
}
```

The note title and body give Mitch full context when he opens the record in Attio: which campaign triggered the reply, when it came in, and the full reply text.

---

### Node 4 — Add to "Interested" List

**Type:** HTTP Request

You need the Attio list ID for your "Interested" list. Find it via:

```
GET https://api.attio.com/v2/lists
```

Identify the list by `name`, grab its `id`. Hardcode this as an n8n credential or environment variable (`ATTIO_INTERESTED_LIST_ID`).

**Add person as list entry:**

```
Method: POST
URL: https://api.attio.com/v2/lists/{{ $credentials.AttioInterestedListId }}/entries

Headers:
  Authorization: Bearer {{ $credentials.AttioApiKey }}
  Content-Type: application/json

Body (JSON):
{
  "data": {
    "record_id": {
      "object": "people",
      "record_id": "{{ $json.person_record_id }}"
    }
  }
}
```

**Duplicate handling:** Attio will return a 409 if the person is already on the list. Add error handling on this node: catch 409 and continue (do not fail the workflow). All other errors should trigger the error handler.

---

### Node 5 — Create Follow-Up Task

**Type:** HTTP Request

```
Method: POST
URL: https://api.attio.com/v2/tasks

Headers:
  Authorization: Bearer {{ $credentials.AttioApiKey }}
  Content-Type: application/json

Body (JSON):
{
  "data": {
    "content": "Follow up with {{ $json.prospect_name || $json.prospect_email }} — replied Interested via {{ $json.campaign_name }}",
    "deadline_at": "{{ DateTime.now().plus({ days: 1 }).toISO() }}",
    "is_completed": false,
    "assignees": [
      {
        "workspace_member_email_address": "mitch@leadgrow.ai"
      }
    ],
    "linked_records": [
      {
        "target_object": "people",
        "target_record_id": "{{ $json.person_record_id }}"
      }
    ]
  }
}
```

**Deadline:** Defaults to 24 hours from now. Adjust the `plus({ days: 1 })` value to match your follow-up SLA.

**Assignee:** Uses `workspace_member_email_address` to assign to Mitch. Confirm this matches the email on his Attio workspace account.

---

### Node 6 — Success Notification

**Type:** Slack (or Write to Log if Slack not available)

On successful completion of Nodes 2-5, post to your ops Slack channel:

```
Channel: #pipeline (or #ops)
Message:
"✅ Interested reply synced to Attio
  Person: {{ $json.prospect_name || $json.prospect_email }}
  Company: {{ $json.prospect_company || 'Unknown' }}
  Campaign: {{ $json.campaign_name }}
  Task created. Reply logged."
```

If you'd rather log than Slack for MVP, write to a file or use n8n's built-in logging.

---

### Node 7 — Error Handler

**Type:** Slack (or log)

Route here from:
- Missing email address (pre-flight check after Node 1)
- Attio API failures (non-409 errors on Nodes 2-5)
- Any unhandled exception

```
Channel: #pipeline (or #errors)
Message:
"⚠️ reply-to-crm workflow failed
  Reply ID: {{ $json.reply_id || 'unknown' }}
  Email: {{ $json.prospect_email || 'MISSING' }}
  Failed at: {{ $execution.lastNodeExecuted }}
  Error: {{ $json.error.message }}"
```

Do not silently fail. If this workflow breaks and nobody notices, pipeline leaks.

---

## Attio API Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| Search person by email | GET | `/v2/objects/people/records?filter[email_addresses][email_address][eq]=...` |
| Create person | POST | `/v2/objects/people/records` |
| Create note | POST | `/v2/notes` |
| List all lists | GET | `/v2/lists` |
| Add to list | POST | `/v2/lists/{list_id}/entries` |
| Create task | POST | `/v2/tasks` |

**Base URL:** `https://api.attio.com`
**Auth:** Bearer token in `Authorization` header. Generate an API key in Attio → Settings → API.
**Attio API docs:** https://developers.attio.com

---

## Error Handling Summary

| Scenario | Behavior |
|----------|----------|
| `prospect_email` missing | Short-circuit after Node 1, notify error channel |
| Person already exists in Attio | Use existing `record_id`, skip create, continue |
| Person already on Interested list | Catch 409 on Node 4, continue (not an error) |
| Attio API returns 401 | Notify error channel — credential issue |
| Attio API returns 5xx | Retry up to 3 times with 5s delay, then notify error |
| Webhook secret mismatch | Reject at Node 1 with 401, do not process |
| Task creation fails | Log warning but do not fail whole workflow — person + note + list are the critical path |

---

## Alternative: attio-cli via Execute Command Node

If n8n is running on the same machine as `attio-cli` (i.e., the LeadGrow workspace), you can replace the HTTP Request nodes with **Execute Command** nodes calling attio-cli directly. This avoids managing raw API calls and handles auth via the CLI's credential store.

Example equivalents:

```bash
# Find or create person
attio people upsert --email jane.doe@acme.com --name "Jane Doe" --company "Acme Corp"

# Create note
attio notes create --person jane.doe@acme.com --title "Interested reply — Campaign Name" --body "Reply text here"

# Add to list
attio lists add --list "Interested" --person jane.doe@acme.com

# Create task
attio tasks create --person jane.doe@acme.com --title "Follow up with Jane Doe" --assignee mitch@leadgrow.ai --due 24h
```

**When to use this approach:**
- n8n is self-hosted on the same machine as attio-cli
- You want to avoid managing Attio API keys separately in n8n
- attio-cli is fully built and tested (verify CLI commands match actual implementation)

**When to use raw HTTP calls:**
- n8n is cloud-hosted (n8n.cloud) and can't reach local CLI
- attio-cli isn't built yet and you need the workflow running now
- You want explicit control over API payloads for debugging

For MVP, use raw HTTP calls. Migrate to attio-cli once the CLI is stable.

---

## Implementation Checklist

- [ ] Register `reply.marked_interested` webhook in EmailBison pointing to n8n webhook URL
- [ ] Store Attio API key in n8n credentials as `AttioApiKey`
- [ ] Identify and store Interested list ID as `AttioInterestedListId`
- [ ] Confirm Mitch's Attio workspace member email for task assignment
- [ ] Set webhook secret and store as n8n credential
- [ ] Test with a real reply — verify person record, note, list entry, and task all appear in Attio
- [ ] Confirm Slack channel is configured for success + error notifications
- [ ] Document the n8n workflow ID for reference in attio-cli docs
