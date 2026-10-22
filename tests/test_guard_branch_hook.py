"""Tests for the Claude Code PreToolUse hook, run the way Claude Code runs it: as a subprocess."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "guard_branch.py"
REPO = {"owner": "acme", "repo": "widgets"}


def run_hook(
    event: object, *, repo: str | None = "acme/widgets"
) -> subprocess.CompletedProcess[str]:
    # Inherit the real environment (Windows needs SystemRoot/SystemDrive) minus harness config.
    env = {k: v for k, v in os.environ.items() if not k.startswith("HARNESS_")}
    if repo is not None:
        env["HARNESS_REPO"] = repo
    return subprocess.run(  # noqa: S603 - fixed interpreter and script path
        [sys.executable, str(HOOK)],
        input=event if isinstance(event, str) else json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


@pytest.mark.parametrize(
    ("tool", "tool_input"),
    [
        ("Read", {"file_path": "x"}),
        ("mcp__github__get_file_contents", {**REPO, "path": "README.md"}),
        ("mcp__github__create_branch", {**REPO, "branch": "harness/3-fix"}),
        ("mcp__github__push_files", {**REPO, "branch": "harness/3-fix", "files": []}),
        ("mcp__github__create_pull_request", {**REPO, "head": "harness/3-fix", "base": "main"}),
        ("mcp__github__issue_write", {**REPO, "method": "update", "issue_number": 3, "labels": []}),
        ("mcp__github__search_code", {"query": "foo repo:acme/widgets"}),
    ],
)
def test_hook_allows_policy_compliant_calls(tool: str, tool_input: dict[str, object]) -> None:
    result = run_hook({"tool_name": tool, "tool_input": tool_input})

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("tool", "tool_input", "reason"),
    [
        ("mcp__github__merge_pull_request", {**REPO, "pullNumber": 1}, "not allowed"),
        ("mcp__github__create_or_update_file", {**REPO, "branch": "main", "path": "a"}, "harness/"),
        ("mcp__github__create_pull_request", {**REPO, "head": "feature/x"}, "harness/"),
        ("mcp__github__create_branch", {**REPO, "branch": "harness/"}, "harness/"),
        (
            "mcp__github__get_file_contents",
            {"owner": "other", "repo": "x", "path": "a"},
            "Only acme/widgets",
        ),
        (
            "mcp__github__issue_write",
            {**REPO, "method": "update", "issue_number": 1, "state": "closed"},
            "labels",
        ),
        ("mcp__github__search_code", {"query": "secret"}, "repo:acme/widgets"),
    ],
)
def test_hook_blocks_policy_violations(
    tool: str, tool_input: dict[str, object], reason: str
) -> None:
    result = run_hook({"tool_name": tool, "tool_input": tool_input})

    assert result.returncode == 2
    assert reason in result.stderr


def test_hook_fails_closed_without_target_repo() -> None:
    result = run_hook({"tool_name": "mcp__github__list_issues", "tool_input": REPO}, repo=None)

    assert result.returncode == 2
    assert "HARNESS_REPO" in result.stderr


def test_hook_fails_closed_on_invalid_json() -> None:
    result = run_hook("not json")

    assert result.returncode == 2
