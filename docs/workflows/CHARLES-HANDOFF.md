---
title: n8n Workflows — Developer Handoff
type: handoff
created: 2026-03-31
---

# n8n Workflows — Developer Handoff

Welcome, Charles. This is your entry point for the 4 n8n automation workflows that connect Attio CRM to the LeadGrow stack.

---

## Overview

**attio-cli** is a Python CLI that wraps the full Attio CRM v2 API. You don't need to touch it. These 4 workflows interact with the Attio API directly via HTTP nodes in n8n — no CLI dependency, no local tooling required.

The workflows sit at the boundary between three systems:

- **EmailBison** — outbound cold email tool. Fires webhooks when replies are marked Interested.
- **Attio** — CRM. Source of truth for people, companies, lists, tasks, and pipeline.
- **Clay** — enrichment and prospecting. Produces enriched contact rows; also receives re-enrichment exports from Attio.

Your job: build the plumbing between them.

---

## Priority Order

| Priority | File | Description | Complexity | Why |
|----------|------|-------------|------------|-----|
| 1 — HIGH | `n8n-reply-to-crm.md` | EmailBison webhook → Attio: create person, log reply as note, add to Interested list, create follow-up task | Medium | Stops pipeline leakage immediately. Every interested reply that doesn't land in Attio is lost revenue. Build this first. |
| 2 — HIGH | `n8n-prospect-intake.md` | Clay → Attio bulk upsert: create/update person + company records, add to outreach list | High | Gate for outreach. Nothing goes to campaign until prospects are in Attio. Required before any campaign goes live. |
| 3 — MEDIUM | `n8n-attio-to-sheets.md` | Weekly scheduled export: pull Attio pipeline, tasks, and lists → write to Google Sheets | Low | Replaces a manual reporting step. Useful but doesn't block anything. |
| 4 — MEDIUM | `n8n-attio-to-clay.md` | Attio list → Clay table via webhook: export contacts for re-enrichment or targeted campaign push | Medium | Lower frequency, ad-hoc use. Build after the intake direction is solid. |

---

## Credentials Charles Needs

Get these from Mitch before starting workflow #1:

| Credential | Where to Find It |
|---|---|
| Attio API key | Attio workspace → Settings → API → Generate key |
| Attio workspace slug / ID | Attio workspace URL or Settings |
| EmailBison webhook secret | Mitch configures this in EmailBison; you set the matching value in n8n |
| Google Sheets service account credentials (or OAuth2) | Mitch's Google Workspace → Service Accounts, or OAuth2 consent flow |
| Clay table webhook URLs | Clay → target table → Integrations → Webhook → copy URL (needed for prospect-intake and attio-to-clay) |
| Slack webhook URL | Mitch's Slack workspace → Apps → Incoming Webhooks |
| Target Attio list IDs | Run `GET https://api.attio.com/v2/lists` with the API key; identify by name, grab the UUID |

Store all secrets in n8n's credential store. Never hardcode in node parameters.

---

## Attio API Basics

| Property | Value |
|---|---|
| Base URL | `https://api.attio.com/v2` |
| Auth header | `Authorization: Bearer {ATTIO_API_KEY}` |
| Content-Type | `application/json` |
| Rate limit | 60 requests/minute |
| Official docs | https://developers.attio.com |

**Rate limit matters for bulk workflows.** `prospect-intake` can generate up to 5 API calls per row (query + company upsert + person create/patch + list assert). At 500 rows, that's ~2,500 calls. Use `SplitInBatches` with a batch size of 10 and a 12-second `Wait` node between batches — this targets ~50 req/min, safely under the cap. The spec has the exact math.

**Attio response shapes:** attribute values are always arrays of objects (e.g., `values.email_addresses[0].email_address`), never bare strings. Read the transform examples in the specs carefully before writing your own.

---

## Questions for Mitch Before Starting

Clarify these before building workflow #1 (`reply-to-crm`):

1. **EmailBison webhook event name** — The spec assumes `reply.marked_interested`. Confirm this is the exact event string fired when a reply is marked Interested in EmailBison.
2. **Target Attio list ID** — Which list should interested contacts be added to? Pull the list UUID via `GET /v2/lists` once you have the API key.
3. **Task assignee** — Follow-up tasks in workflow #1 are assigned to Mitch. Confirm his email address as it appears in the Attio workspace (used as `workspace_member_email_address`).
4. **Error alerting preference** — Should failed webhook deliveries post to Slack immediately, or just log to n8n's execution history? The spec has Slack wired in by default; confirm the channel name and whether Mitch wants it active from day one.

---

## Spec Files

| File | Description |
|---|---|
| `n8n-reply-to-crm.md` | Full node sequence for the EmailBison → Attio interested reply sync: webhook trigger, person find-or-create, note creation, list add, task creation, error handling. |
| `n8n-prospect-intake.md` | Bulk Clay → Attio upsert spec: three trigger options (Clay webhook, Sheets poll, CSV), per-row create/update logic, rate limit strategy, summary report format. |
| `n8n-attio-to-sheets.md` | Weekly export spec: three parallel Attio data pulls (pipeline, tasks, lists), JavaScript transform examples, Google Sheets tab layout with exact column mappings, stale data detection. |
| `n8n-attio-to-clay.md` | Reverse export spec: Attio list → Clay table via POST webhook, field mapping configuration, pagination, per-row retry logic, summary output. |

Each spec is self-contained and includes API call examples, error handling tables, and an implementation checklist. Start with the spec for the workflow you're building — everything you need is in there.
