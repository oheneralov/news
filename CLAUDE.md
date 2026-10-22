# Claude Code harness

In this directory, Claude Code is the harness. GitHub is the system of record and you reach it
only through the `github` MCP server. You do not have a local checkout of the target repository.
Read and write it with the MCP tools.

The target repository is the one in the `HARNESS_REPO` environment variable (`owner/name`).

## System of record
- **Tasks** are open issues labelled `ai-task`.
- **Context** lives in the target repository:
  - `.harness/context.md` is harness-owned durable knowledge. Keep it current.
  - `AGENTS.md` and `CLAUDE.md` are written by humans. Read them, but do not edit them.
- **Delivery** is a pull request from a `harness/<issue>-<slug>` branch. A human reviews and merges it.
- **Status** goes back on the issue: a comment when you start and when you finish. When you finish, also change the label from `ai-task` to `ai-in-review`, or to `ai-failed` if the run failed.

## Rules
- Never write to the default branch, never merge, and never delete. The hook in `.claude/hooks/guard_branch.py` blocks these, and so do the permission deny rules.
- Make the smallest change that fully solves the issue, and follow the target repo's conventions.
- When you learn something durable, such as a decision, a convention, or a gotcha, add it to `.harness/context.md` in the same PR. Task-specific notes do not belong there.
- If an issue is unclear, comment on the issue with your questions instead of guessing.

## Commands
- `/next-task`: pick the oldest `ai-task` issue, load the context, and propose a plan.
- `/ship <issue>`: implement the plan on a harness branch, open the PR, and report on the issue.
- `/sync-context`: review `.harness/context.md` against recent merged PRs and propose updates via a PR.

The same workflows also exist as skills in `.claude/skills/`: `harness-next-task`, `harness-ship` and `harness-sync-context`. Keep each skill in step with its command.
