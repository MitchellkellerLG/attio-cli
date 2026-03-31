# Roadmap: Attio CLI

## Overview

Three phases to a fully agent-controllable Attio CLI. Phase 1 builds the foundation layers and validates the full stack through Records end-to-end. Phase 2 repeats the established pattern across all 11 remaining resource groups to achieve complete API coverage. Phase 3 adds the REPL, the test suite, and documentation to make the tool production-ready and discoverable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation + Records** - Build all architectural layers and validate end-to-end with Records CRUD
- [ ] **Phase 2: Full API Coverage** - Replicate the established pattern across all remaining resource groups
- [ ] **Phase 3: REPL, Tests, and Docs** - Interactive mode, test suite, and agent-discovery documentation

## Phase Details

### Phase 1: Foundation + Records
**Goal**: Users can authenticate and run full CRUD, search, and pagination against Attio Records from the CLI
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07, INFRA-08, INFRA-09, INFRA-10, INFRA-11, INFRA-12, INFRA-13, INFRA-14, REC-01, REC-02, REC-03, REC-04, REC-05, REC-06, REC-07, REC-08, REC-09, REC-10
**Success Criteria** (what must be TRUE):
  1. User can run `attio people list` and receive a Rich table in the terminal or JSON when piped
  2. User can create, get, update (PATCH and PUT), delete, assert, and search records against any standard object
  3. `--all` flag streams all pages without buffering; `--limit N` caps results
  4. Invalid API key surfaces a clear auth error with exit code 4; 429s retry with backoff automatically
  5. Every command has `--help` output and `--json` flag; auth header never appears in error output
**Plans**: 6 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffold: setup.py, pyproject.toml, directory structure, conftest.py
- [x] 01-02-PLAN.md — Core utils: config.py (XDG config, env var precedence) + exceptions.py (semantic exit codes)
- [x] 01-03-PLAN.md — Formatter: format_output, format_error, format_pagination_footer + test_formatter.py
- [x] 01-04-PLAN.md — AttioClient: httpx, tenacity retry/backoff, offset pagination generator + test_client.py
- [x] 01-05-PLAN.md — Records commands: people/companies/deals/users/workspaces/records groups + attio_cli.py entry point + test_commands.py
- [x] 01-06-PLAN.md — Config subcommand (set/get/path/list) + shell completion wiring

### Phase 2: Full API Coverage
**Goal**: Every Attio API endpoint has a corresponding CLI command following the pattern established in Phase 1
**Depends on**: Phase 1
**Requirements**: NOTE-01, NOTE-02, NOTE-03, NOTE-04, NOTE-05, TASK-01, TASK-02, TASK-03, TASK-04, TASK-05, CMNT-01, CMNT-02, CMNT-03, CMNT-04, CMNT-05, CMNT-06, LIST-01, LIST-02, LIST-03, LIST-04, LIST-05, ENTRY-01, ENTRY-02, ENTRY-03, ENTRY-04, ENTRY-05, ENTRY-06, ENTRY-07, OBJ-01, OBJ-02, OBJ-03, OBJ-04, OBJ-05, ATTR-01, ATTR-02, ATTR-03, ATTR-04, ATTR-05, ATTR-06, FILE-01, FILE-02, FILE-03, FILE-04, FILE-05, FILE-06, MEET-01, MEET-02, MEET-03, MEET-04, HOOK-01, HOOK-02, HOOK-03, HOOK-04, HOOK-05, WORK-01, WORK-02, WORK-03
**Success Criteria** (what must be TRUE):
  1. User can create, list, get, update, and delete notes and tasks on records
  2. User can manage lists and list entries (CRUD, assert, PATCH vs PUT) with the same filter/sort/pagination interface as records
  3. User can list, create, and update objects and attributes; `attio attributes archive` works; no `attributes delete` command exists
  4. User can upload, download, and manage files; list meetings and retrieve transcripts; manage webhook subscriptions; list workspace members
  5. `attio comments create/get/delete/resolve/unresolve` and `attio threads list/get` all function correctly
**Plans**: 6 plans

Plans:
- [ ] 02-01-PLAN.md — Notes + Tasks: client methods, command files, tests, CLI registration
- [ ] 02-02-PLAN.md — Comments + Threads: client methods, command files (resolve/unresolve), tests, CLI registration
- [ ] 02-03-PLAN.md — Lists + List Entries: CRUD, assert, PATCH/PUT, filter/pagination, tests, CLI registration
- [ ] 02-04-PLAN.md — Objects + Attributes: list/get/create/update, archive (no delete), options, statuses, tests, CLI registration
- [ ] 02-05-PLAN.md — Files (binary upload/download) + Meetings (read-only, transcripts), tests, CLI registration
- [ ] 02-06-PLAN.md — Webhooks + Workspace Members + full test suite verification

### Phase 3: REPL, Tests, and Docs
**Goal**: The CLI has an interactive REPL, a passing test suite, and documentation that makes it agent-discoverable
**Depends on**: Phase 2
**Requirements**: REPL-01, REPL-02, REPL-03, REPL-04, REPL-05, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, DOC-01, DOC-02, DOC-03
**Success Criteria** (what must be TRUE):
  1. `attio repl` starts an interactive session with arrow-key history, tab completion of commands, and graceful error recovery (no crash on bad command)
  2. `--yes` flag suppresses all confirmation prompts for non-interactive/agent use
  3. `pytest` passes all unit tests with no real API calls (pytest-httpx mocks); E2E tests against LeadGrow workspace pass
  4. SKILL.md exists and is loadable for AI agent discovery; ATTIO.md SOP exists with usage examples
  5. `pip install -e .` registers the `cli-anything-attio` entry point and the CLI is usable as a package
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation + Records | 6/6 | Complete |  |
| 2. Full API Coverage | 0/6 | Planning complete | - |
| 3. REPL, Tests, and Docs | 0/? | Not started | - |
