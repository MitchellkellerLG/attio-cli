"""E2E tests against the live Attio API (LeadGrow workspace).

These tests are skipped unless ATTIO_API_KEY is set in the environment.
To run: ATTIO_API_KEY=<key> pytest agent-harness/cli_anything/attio/tests/test_e2e.py -v

The CLI under test loads config via its own load_config() which reads ATTIO_API_KEY
from env or ~/.config/attio/config.toml — no special mock setup is needed here.
"""
import json
import os

import pytest
from click.testing import CliRunner

from cli_anything.attio.attio_cli import cli

pytestmark = pytest.mark.skipif(
    not os.getenv("ATTIO_API_KEY"),
    reason="ATTIO_API_KEY not set — skipping E2E tests",
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestE2EWorkspace:
    def test_workspace_self_returns_json(self, runner: CliRunner) -> None:
        """GET /v2/self — workspace identity endpoint returns valid JSON."""
        result = runner.invoke(cli, ["workspace", "self", "--json"])
        assert result.exit_code == 0, f"Unexpected exit: {result.output}"
        data = json.loads(result.output.strip())
        assert isinstance(data, dict), "Expected a JSON object"

    def test_workspace_members_returns_list(self, runner: CliRunner) -> None:
        """GET /v2/workspace_members — returns a JSON object with a data list."""
        result = runner.invoke(cli, ["workspace", "members", "--json"])
        assert result.exit_code == 0, f"Unexpected exit: {result.output}"
        data = json.loads(result.output.strip())
        assert isinstance(data, dict) and "data" in data, "Expected a JSON object with 'data' key"


class TestE2EPeople:
    def test_people_list_returns_records(self, runner: CliRunner) -> None:
        """GET /v2/objects/people/records — returns records list (limit 1)."""
        result = runner.invoke(cli, ["people", "list", "--json", "--limit", "1"])
        assert result.exit_code == 0, f"Unexpected exit: {result.output}"
        # Output may be a JSON array or newline-delimited JSON objects
        first_line = result.output.strip().split("\n")[0]
        data = json.loads(first_line)
        assert isinstance(data, (dict, list)), "Expected JSON output"


class TestE2ENotes:
    def test_notes_list_returns_json(self, runner: CliRunner) -> None:
        """GET /v2/notes — returns notes list."""
        result = runner.invoke(cli, ["notes", "list", "--json", "--limit", "5"])
        assert result.exit_code == 0, f"Unexpected exit: {result.output}"
        # Empty workspace is valid — just confirm exit code and valid JSON shape
        output = result.output.strip()
        if output:
            first_line = output.split("\n")[0]
            json.loads(first_line)  # Raises on invalid JSON


class TestE2ETasks:
    def test_tasks_list_returns_json(self, runner: CliRunner) -> None:
        """GET /v2/tasks — returns tasks list."""
        result = runner.invoke(cli, ["tasks", "list", "--json", "--limit", "5"])
        assert result.exit_code == 0, f"Unexpected exit: {result.output}"
        output = result.output.strip()
        if output:
            first_line = output.split("\n")[0]
            json.loads(first_line)  # Raises on invalid JSON
