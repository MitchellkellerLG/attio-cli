# Attio CLI

## What This Is

A CLI built with the CLI-Anything framework that wraps the entire Attio CRM REST API (v2). Gives AI agents and power users full command-line access to Attio — records, lists, notes, tasks, deals, meetings, webhooks, and everything else the API exposes. Built for the LeadGrow.ai workspace but works with any Attio workspace.

## Core Value

Every Attio API operation accessible as a typed, documented CLI command with JSON output and interactive REPL — making Attio fully agent-controllable.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Auth: API key configuration via env var or config file, token validation via /v2/self
- [ ] Records CRUD: Create, get, list/query, update (PUT + PATCH), delete, assert, search for all standard objects (people, companies, deals, users, workspaces)
- [ ] Custom Objects: List, create, get, update objects; manage views
- [ ] Attributes: List, create, update attributes on objects/lists; manage select options and statuses
- [ ] Lists: List, create, get, update lists; manage views
- [ ] List Entries: Create, get, list/query, update (PUT + PATCH), delete, assert entries
- [ ] Notes: Create, get, list, update, delete notes on records
- [ ] Tasks: Create, get, list, update, delete tasks with assignees and linked records
- [ ] Comments & Threads: Create, get, delete comments; list/get threads; resolve/unresolve
- [ ] Files: Upload, get, list, download, delete files; create folders
- [ ] Meetings: Get, list meetings; get call recordings and transcripts
- [ ] Webhooks: Create, get, list, update, delete webhook subscriptions
- [ ] Workspace Members: List and get workspace members
- [ ] Filtering & Sorting: Support Attio's filter/sort syntax on all query endpoints
- [ ] Pagination: Automatic pagination (cursor + offset) with --limit and --all flags
- [ ] JSON Output: All commands support --json flag for structured output
- [ ] REPL Mode: Interactive session with state management, history, tab completion
- [ ] Error Handling: Rate limit awareness (429 retry), clear error messages, exit codes

### Out of Scope

- OAuth flow implementation — API key auth only (LeadGrow is single-workspace)
- SCIM provisioning — enterprise-only feature we don't use
- GUI or TUI — this is a CLI, not a dashboard
- Webhook receiver/server — CLI manages subscriptions, doesn't host endpoints

## Context

- **API Base**: https://api.attio.com/v2
- **Auth**: Bearer token (API key), full read-write scopes confirmed
- **Rate Limits**: 100 reads/sec, 25 writes/sec. 429 responses include Retry-After header
- **Pagination**: Cursor-based (preferred) and offset-based. Default limit 500
- **Framework**: CLI-Anything (Python 3.10+, Click 8.0+, prompt-toolkit 3.0+, pytest)
- **OpenAPI Spec**: https://api.attio.com/openapi/api (machine-readable, source of truth)
- **Workspace**: LeadGrow.ai (workspace_id: f3f2c1b6-c744-4505-be12-1d5584a5e31f)
- **Existing CLIs in CLI-Anything**: 16+ apps (GIMP, Blender, OBS, etc.) — follow their patterns

## Constraints

- **Tech stack**: Python 3.10+, Click, prompt-toolkit, pytest (CLI-Anything requirements)
- **API version**: v2 only (v1 deprecated)
- **Auth method**: API key only (no OAuth complexity for single-workspace use)
- **Output format**: All commands must support --json for agent consumption
- **Testing**: Unit + E2E tests required (CLI-Anything standard)
- **Structure**: Must follow CLI-Anything directory conventions (agent-harness/, cli_anything/attio/, etc.)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| API key auth only, no OAuth | Single workspace use, OAuth adds complexity with no value for our case | — Pending |
| CLI-Anything framework | Proven framework (16+ apps, 2000+ tests), AI-agent-native design | — Pending |
| Full API coverage | "Everything their API can do" — no partial implementation | — Pending |
| Coarse phase structure | Infrastructure project, not a product — broader phases ship faster | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-30 after initialization*
