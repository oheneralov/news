"""Claude Code PreToolUse hook enforcing the harness policy on GitHub MCP tool calls.

Reads the hook event as JSON on stdin. Exit code 0 allows the call; exit code 2 blocks it
and the reason on stderr is shown to Claude.

This mirrors ``harness_core.guard.Policy`` deliberately: hooks run with a bare Python
interpreter, so this file must stay dependency-free. Keep the two in sync.

Environment:
    HARNESS_REPO           owner/name the session may touch (required)
    HARNESS_BRANCH_PREFIX  prefix for every branch written to (default: harness/)
"""

import json
import os
import sys
from collections.abc import Mapping

MCP_PREFIX = "mcp__github__"

DENIED_TOOLS = frozenset(
    {"merge_pull_request", "delete_file", "delete_repository", "fork_repository"}
)
SEARCH_TOOLS = frozenset({"search_code", "search_issues", "search_pull_requests"})
BRANCH_WRITE_TOOLS: Mapping[str, str] = {
    "create_branch": "branch",
    "create_or_update_file": "branch",
    "push_files": "branch",
    "create_pull_request": "head",
}
LABEL_TOOLS: Mapping[str, frozenset[str]] = {
    "issue_write": frozenset({"method", "owner", "repo", "issue_number", "labels"}),
    "update_issue": frozenset({"owner", "repo", "issue_number", "labels"}),
}


def check(tool_name: str, tool_input: Mapping[str, object], repo: str, prefix: str) -> str | None:
    """Return why the call is blocked, or ``None`` to allow it."""
    if not tool_name.startswith(MCP_PREFIX):
        return None
    tool = tool_name.removeprefix(MCP_PREFIX)
    if tool in DENIED_TOOLS:
        return f"'{tool}' is not allowed by the harness policy; a human merges and deletes."
    if tool in SEARCH_TOOLS:
        query = tool_input.get("query")
        scope = f"repo:{repo}".casefold()
        if not isinstance(query, str) or scope not in query.casefold().split():
            return f"Search queries must include 'repo:{repo}'."
        return None

    owner, name = tool_input.get("owner"), tool_input.get("repo")
    targets_a_repo = owner is not None or name is not None
    if targets_a_repo and f"{owner}/{name}".casefold() != repo.casefold():
        return f"Only {repo} may be accessed in this harness."

    if tool in BRANCH_WRITE_TOOLS:
        branch = tool_input.get(BRANCH_WRITE_TOOLS[tool])
        if not isinstance(branch, str) or not branch.startswith(prefix) or branch == prefix:
            return f"Writes are only allowed on branches starting with '{prefix}'."
        if ".." in branch:
            return "Invalid branch name."
    if tool in LABEL_TOOLS:
        extra = set(tool_input) - LABEL_TOOLS[tool]
        if extra or (tool == "issue_write" and tool_input.get("method") != "update"):
            return "Issue updates may only change labels."
    return None


def main() -> int:
    repo = os.environ.get("HARNESS_REPO", "")
    if "/" not in repo:
        print("HARNESS_REPO (owner/name) must be set for the harness hook.", file=sys.stderr)
        return 2
    prefix = os.environ.get("HARNESS_BRANCH_PREFIX", "harness/")
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Harness hook received invalid JSON.", file=sys.stderr)
        return 2
    reason = check(str(event.get("tool_name", "")), event.get("tool_input") or {}, repo, prefix)
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
