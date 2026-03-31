# Stack Research

**Domain:** API CLI wrapper (Attio CRM)
**Researched:** 2026-03-30
**Confidence:** HIGH — all versions verified against PyPI/official docs as of research date

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10+ | Runtime | CLI-Anything hard requirement. 3.10 structural pattern matching is useful for response dispatch. No deviation. |
| Click | 8.3.1 | CLI framework | CLI-Anything hard requirement. Declarative command/option/argument structure, built-in shell completion, CliRunner for testing. 8.3.x is current stable. |
| prompt-toolkit | 3.0.52 | REPL + interactive input | CLI-Anything hard requirement. Powers the interactive REPL mode — history, completion, key bindings. Already a transitive dep if you use ipython/rich; pin explicitly. |
| httpx | 0.28.1 | HTTP client | Sync-first with async capability. Attio's CLI is synchronous by design, but rate-limit retry logic benefits from a clean transport layer. httpx's `Client` is a drop-in upgrade from requests with connection pooling, HTTP/2, and a composable transport layer that makes mocking trivial in tests. `requests` is synchronous-only and has no built-in transport interface for test doubles — skip it. |
| tenacity | 9.1.4 | Retry / backoff | Best-in-class Python retry library. Handles Attio's 429 + `Retry-After` header pattern with `wait_fixed` + `retry_if_exception_type` + exponential backoff + jitter. Cleaner than hand-rolling retry loops. Async-compatible if needed later. |
| rich | 14.3.3 | Terminal output | Tables, colored output, progress bars, syntax-highlighted JSON. Required for human-readable display mode. Pairs with `--json` flag (rich off, raw JSON on). Active release cadence; 14.x is the current major. |
| python-dotenv | 1.2.2 | Env/config loading | Load `ATTIO_API_KEY` and workspace config from `.env` file. 12-factor compliant, zero magic, no type system overhead. Simpler than pydantic-settings for a single-config-value CLI. |
| pytest | 7.0+ | Testing framework | CLI-Anything hard requirement. Use with `click.testing.CliRunner` for command invocation tests. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-httpx | 0.35+ | Mock httpx in tests | Use in all unit tests that invoke HTTP calls. Provides `HTTPXMock` fixture — add canned responses, assert requests were made. Eliminates real network calls in CI. |
| rich-click | 1.9+ | Rich-formatted help text | Drop `import click` in favor of `import rich_click as click` in the main CLI entry point only. Delivers formatted help output (grouped commands, styled options) for free, with zero API changes. Does NOT replace rich for output — just improves `--help` rendering. |
| click-repl | 0.3.0 | REPL loop wiring | Bridges Click's command tree into prompt-toolkit's interactive loop. Provides command history, `!` shell escapes, and `:help` meta-commands inside the REPL. Use in `repl.py` module. Avoids hand-writing the REPL dispatch loop. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Fast package management + virtualenv | Use `uv venv` + `uv pip install`. Dramatically faster than pip, handles resolution better. No code changes required. |
| ruff | Linting + formatting | Single tool replaces flake8 + isort + black. Run in pre-commit and CI. |
| mypy | Type checking | Click 8.x is fully typed; httpx and rich are typed. Enforce strict mode from day one — retrofitting types onto a large CLI is painful. |
| pre-commit | Git hooks | Run ruff + mypy before every commit. Catches issues before they hit CI. |
| pytest-cov | Coverage reporting | Track coverage across unit and E2E test suites. CLI-Anything standard is high coverage. |

---

## Installation

```bash
# Core runtime
pip install httpx tenacity rich python-dotenv rich-click click-repl

# Testing
pip install pytest pytest-httpx pytest-cov

# Dev tooling (not in package deps)
pip install ruff mypy pre-commit
```

Or as `pyproject.toml` dependencies:

```toml
[project]
requires-python = ">=3.10"
dependencies = [
    "click>=8.3.1",
    "prompt-toolkit>=3.0.52",
    "httpx>=0.28.1",
    "tenacity>=9.1.4",
    "rich>=14.3.3",
    "rich-click>=1.9",
    "click-repl>=0.3.0",
    "python-dotenv>=1.2.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-httpx>=0.35",
    "pytest-cov",
    "ruff",
    "mypy",
    "pre-commit",
]
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| HTTP client | httpx | requests | requests is synchronous-only, no composable transport for mocking, no HTTP/2. httpx has equivalent sync API with none of the limitations. Switching later is painful. |
| HTTP client | httpx | aiohttp | aiohttp is async-only. This CLI is synchronous. Using aiohttp here adds async overhead everywhere for zero benefit. |
| Retry | tenacity | stamina | stamina is a thin tenacity wrapper with opinionated defaults. Tenacity gives finer-grained control over Attio's specific 429 + Retry-After pattern. Either would work; tenacity is more widely understood. |
| Config | python-dotenv | pydantic-settings | pydantic-settings is the right call for web apps with complex nested config. For a CLI with one API key and one base URL, it's architectural overreach. python-dotenv + manual `os.getenv()` is direct and debuggable. |
| Output formatting | rich | colorama + tabulate | Two dependencies instead of one, and combined they don't match rich's table rendering quality. No reason to use them when rich exists. |
| Help text | rich-click | Click default | Click's default help is functional but plain. rich-click costs nothing to adopt (single import swap) and makes the CLI look professional when agents or humans call `--help`. |
| REPL | click-repl | hand-rolled prompt-toolkit loop | CLI-Anything already mandates prompt-toolkit. click-repl is the standard integration layer between Click and prompt-toolkit. Writing your own dispatch loop is 200 lines of code that click-repl already got right. |
| Package manager | uv | pip | pip works but uv is 10-100x faster for resolution. No impact on deliverables — just developer experience. Both produce identical installs. |

---

## What NOT to Use

**aiohttp** — async-only, requires `asyncio` everywhere. This CLI is synchronous. Don't introduce async complexity for a single-user CLI with sequential request patterns.

**typer** — a popular Click wrapper that generates Click apps from type hints. CLI-Anything's existing harnesses use Click directly. Using typer would break pattern consistency with the framework and add a dependency that generates Click objects anyway. Use Click directly.

**pydantic** (for config) — justified in web apps, wrong here. A CLI with one API key does not need a validation layer for environment variables. python-dotenv + a single `get_api_key()` function is the correct scope.

**requests** — still the most-used HTTP library by volume, but wrong for new projects in 2026. No async path, no composable transport, worse test ergonomics than httpx. httpx is its direct successor with a nearly identical API.

**click-completion** (click-contrib) — abandoned. Use Click 8's built-in `shell_completion` module instead. Click 8 ships native bash/zsh/fish completion — no third-party package needed.

**PyYAML for config files** — TOML (`tomllib`, stdlib in Python 3.11+) or simple `.env` files are sufficient. A YAML config layer adds parser complexity for no benefit in a single-user CLI.

---

## Notes on CLI-Anything Constraints

The framework mandates Click, prompt-toolkit, and pytest. Everything else in this stack was chosen to complement those constraints without fighting them:

- httpx's sync `Client` looks identical to requests' `Session` — existing CLI-Anything contributors can read it immediately.
- tenacity decorates functions; it doesn't change call signatures. Drop it on the `_request()` helper and the rest of the codebase is unaware it exists.
- rich is used exclusively for human-readable output. The `--json` flag bypasses it entirely, outputting raw JSON to stdout. This keeps agent-consumption clean.
- pytest-httpx integrates with pytest natively — no new fixtures or plugins to learn beyond adding `httpx_mock` to test function signatures.

---

## Sources

- httpx current version (0.28.1): [httpx PyPI](https://pypi.org/project/httpx/)
- tenacity current version (9.1.4): [tenacity PyPI](https://pypi.org/project/tenacity/) | [tenacity docs](https://tenacity.readthedocs.io/en/stable/)
- rich current version (14.3.3): [rich PyPI](https://pypi.org/project/rich/) | [rich docs](https://rich.readthedocs.io/en/latest/introduction.html)
- click current version (8.3.1): [click PyPI](https://pypi.org/project/click/) | [click docs](https://click.palletsprojects.com/en/stable/)
- prompt-toolkit current version (3.0.52): [prompt-toolkit PyPI](https://pypi.org/project/prompt-toolkit/)
- python-dotenv current version (1.2.2): [python-dotenv PyPI](https://pypi.org/project/python-dotenv/)
- rich-click v1.9: [rich-click GitHub](https://github.com/ewels/rich-click) | [v1.9 release notes](https://ewels.github.io/rich-click/latest/blog/2025/09/16/version-1.9/)
- pytest-httpx: [pytest-httpx PyPI](https://pypi.org/project/pytest-httpx/) | [docs](https://colin-b.github.io/pytest_httpx/)
- httpx vs requests comparison: [Speakeasy analysis](https://www.speakeasy.com/blog/python-http-clients-requests-vs-httpx-vs-aiohttp) | [Towards Data Science](https://towardsdatascience.com/beyond-requests-why-httpx-is-the-modern-http-client-you-need-sometimes/)
- CLI-Anything framework: [GitHub](https://github.com/HKUDS/CLI-Anything) | [QUICKSTART](https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/QUICKSTART.md) | [CONTRIBUTING](https://github.com/HKUDS/CLI-Anything/blob/main/CONTRIBUTING.md)
- tenacity retry patterns: [OpenAI rate limit cookbook](https://cookbook.openai.com/examples/how_to_handle_rate_limits) | [tenacity guide](https://leapcell.io/blog/enhancing-python-applications-with-tenacity)
- pydantic-settings vs python-dotenv: [FastAPI settings guide](https://fastapi.tiangolo.com/advanced/settings/)
