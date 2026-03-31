# Phase 1: Foundation + Records - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 01-foundation-records
**Areas discussed:** Command Hierarchy, Update Semantics, Filter Input, Config Location, Error Verbosity
**Mode:** Auto (all areas auto-selected, recommended defaults chosen)

---

## Command Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Per-object groups | `attio people list`, `attio companies get` — one Click group per object | ✓ |
| Single records group | `attio records list people` — generic group with object as argument | |
| Hybrid | Both available, standard objects as aliases | |

**User's choice:** [auto] Per-object groups (recommended default)
**Notes:** Maps 1:1 to Attio API taxonomy. Generic `attio records` group also available for custom objects.

---

## Update Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| PATCH default + --overwrite | Single update command, safe default, explicit opt-in for replacement | ✓ |
| Separate update/overwrite | Two distinct commands for each verb | |
| PUT default | Replace by default, --append for additive | |

**User's choice:** [auto] PATCH default + --overwrite flag (recommended default)
**Notes:** Safer default prevents silent data loss on multiselect attributes. Pitfalls research confirmed this is critical.

---

## Filter Input

| Option | Description | Selected |
|--------|-------------|----------|
| Triple interface | key=value shorthand + --filter-file + raw JSON | ✓ |
| JSON only | --filter '{json}' for all cases | |
| File only | --filter-file path.json exclusively | |

**User's choice:** [auto] Triple interface (recommended default)
**Notes:** Covers simple, complex, and agent use cases. Shell quoting is a known pitfall from research.

---

## Config Location

| Option | Description | Selected |
|--------|-------------|----------|
| XDG ~/.config/attio/ | Standard location, clean home directory | ✓ |
| ~/.attio/ | Simpler, dotfile convention | |
| Project-local .attio/ | Per-project config | |

**User's choice:** [auto] XDG ~/.config/attio/ (recommended default)
**Notes:** Modern CLI convention. Security research recommends not storing config in project directories.

---

## Error Verbosity

| Option | Description | Selected |
|--------|-------------|----------|
| Contextual with hints | Actionable messages suggesting next commands | ✓ |
| Minimal | Error code + short message only | |
| Verbose | Full HTTP response details | |

**User's choice:** [auto] Contextual with hints (recommended default)
**Notes:** Agents get parseable exit codes, humans get actionable suggestions. --verbose flag available separately for HTTP debugging (v2).

---

## Claude's Discretion

- Table column selection for Rich output
- Progress indicator style
- Config subcommand design
- Test fixture organization
- Module import structure
