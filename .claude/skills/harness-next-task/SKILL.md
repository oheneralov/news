---
name: harness-next-task
description: Pick the next ai-task issue, load repo context, and propose a plan. Use when the user asks what to work on next, or to plan an ai-task issue in the target repository.
argument-hint: "[issue]"
allowed-tools: Bash(echo:*), mcp__github__list_issues, mcp__github__issue_read, mcp__github__get_issue, mcp__github__get_file_contents, mcp__github__search_code
---

Target repository: !`echo "$HARNESS_REPO"`. Issue to use, if one was given: $ARGUMENTS

1. If no issue number was given, list the open issues labelled `ai-task` and pick the one with the lowest number.
2. Read the issue in full.
3. Read `.harness/context.md`, `AGENTS.md` and `CLAUDE.md` from the default branch. Skip any that are missing.
4. Read the files most relevant to the issue. Use `search_code` with `repo:<owner>/<name>` in the query.
5. Reply with a concise plan. Include:
   - the issue number and title,
   - the branch name, as `harness/<issue>-<slug>` with a slug of lowercase words joined by dashes, at most 40 characters,
   - the files you will change, and how,
   - any open questions.

Do not change anything yet. When the user approves the plan, they will run `/harness-ship <issue>` (or `/ship <issue>`).
