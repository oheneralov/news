# Harness context

## Repository
- The default branch is `harness_claude_code`; there is no `main`. Create harness branches from it and open PRs against it. A PR with `base: main` fails with `PullRequest.base (invalid)`.

## Commands and skills
- Each harness workflow exists twice: as a command in `.claude/commands/` and as a skill in `.claude/skills/` (`next-task` / `harness-next-task`, `ship` / `harness-ship`, `sync-context` / `harness-sync-context`). Change both together.
- Utility skills that are not harness workflows, such as `git-push-all`, are skill-only and have no matching command.
- Skills that write or push (`harness-ship`, `harness-sync-context`, `git-push-all`) set `disable-model-invocation: true`, so they run only when a user types them.
