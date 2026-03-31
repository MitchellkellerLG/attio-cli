# Phase 1: Foundation + Records - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Build all architectural layers (config, HTTP client, formatter, entry point) and validate end-to-end with Records CRUD. After this phase, `attio people list`, `attio companies create`, `attio deals get <id>` all work with pagination, rate limiting, JSON output, and semantic exit codes.

</domain>

<decisions>
## Implementation Decisions

### Command Hierarchy
- **D-01:** Per-object top-level groups. `attio people list`, `attio companies get <id>`, `attio deals create`. Each standard object is a Click group. Maps 1:1 to Attio's API taxonomy.
- **D-02:** Generic `attio records` group also available for custom objects: `attio records list <object-slug>`. Standard objects are aliases for convenience.

### Update Semantics
- **D-03:** Single `update` command per object. PATCH by default (appends multiselect values). `--overwrite` flag switches to PUT (replaces multiselect values).
- **D-04:** Assert command (`attio people assert`) uses `--matching-attribute <slug>` to specify the match key. Warn in help text about multiselect asymmetry (matching attribute = additive, payload attributes = replacement).

### Filter Input
- **D-05:** Triple filter interface: `--filter key=value` for simple equality, `--filter-file path.json` for complex filters, and raw `--filter '{json}'` for inline JSON. `@path.json` prefix accepted as shorthand for file path.
- **D-06:** When filter JSON parsing fails, emit helpful error with shell-escaping example for the detected shell.

### Config & Auth
- **D-07:** XDG-compliant config at `~/.config/attio/config.json`. REPL history at `~/.config/attio/history`. Never write config to working directory.
- **D-08:** `ATTIO_API_KEY` env var always takes precedence over config file. Config file stores API key + base URL override.
- **D-09:** Validate API key on first command (not every command) via `GET /v2/self`. Cache validation result for session.

### Error Handling
- **D-10:** Contextual errors with actionable hints. Auth errors suggest `attio config set api-key`. 404s suggest the relevant list command. Rate limits show retry countdown to stderr.
- **D-11:** Authorization header redacted from all error output. Never log raw request objects.
- **D-12:** Retry on 429 (exponential backoff + Retry-After + jitter) AND on 500/502/503/504 (transient server errors). Max 3 retries.

### Output
- **D-13:** TTY-aware defaults: Rich tables when stdout is a terminal, JSON when piped. `--json` flag forces JSON regardless.
- **D-14:** Streaming pagination for `--all` flag. Output records page-by-page, never buffer all pages. Progress indicator to stderr.
- **D-15:** When results are paginated and `--all` not used, show footer: "(showing N results — use --all to fetch all pages)". In JSON mode, include `"has_more": true`.

### Claude's Discretion
- Table column selection for Rich output (which fields to show by default per object type)
- Progress indicator style (spinner vs count vs dots)
- `attio config` subcommand design (set/get/list/path)
- Test fixture organization
- Module import structure within cli_anything/attio/

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Attio API
- `.planning/research/STACK.md` — Locked technology stack with versions
- `.planning/research/ARCHITECTURE.md` — Component boundaries, data flow, build order
- `.planning/research/PITFALLS.md` — Critical pitfalls (PUT/PATCH, score-based rate limits, pagination memory)
- `.planning/research/FEATURES.md` — Table stakes vs differentiators, feature dependencies

### Framework
- CLI-Anything HARNESS.md (remote): https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/HARNESS.md — Framework conventions
- CLI-Anything CONTRIBUTING.md (remote): https://github.com/HKUDS/CLI-Anything/blob/main/CONTRIBUTING.md — Code standards

### API Reference
- Attio OpenAPI spec (remote): https://api.attio.com/openapi/api — Machine-readable endpoint definitions
- Attio Rate Limiting (remote): https://docs.attio.com/rest-api/guides/rate-limiting — Score-based limits
- Attio Pagination (remote): https://docs.attio.com/rest-api/guides/pagination — Cursor + offset patterns
- Attio Filtering (remote): https://docs.attio.com/rest-api/guides/filtering-and-sorting — Filter DSL

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- CLI-Anything convention: `cli_anything/<app>/<app>_cli.py` as main entry point
- CLI-Anything convention: `utils/<app>_backend.py` for backend logic (maps to `utils/attio_client.py`)
- Click `ctx.obj` pattern for shared state across command groups

### Integration Points
- `setup.py` entry_points registers `cli-anything-attio` console script
- `.env` file at workspace root (`Everything_CC/.env`) contains `ATTIO_API_KEY`

</code_context>

<specifics>
## Specific Ideas

- API key confirmed working: `ATTIO_API_KEY` in `Everything_CC/.env`, full read-write scopes, workspace "LeadGrow.ai"
- Existing FroeMic/attio-cli covers ~40 endpoints — our differentiator is full 70+ coverage
- httpx over requests is locked (research verified)
- Attribute types have type-specific write formats — type-aware coercion needed for record creates/updates

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-records*
*Context gathered: 2026-03-31*
