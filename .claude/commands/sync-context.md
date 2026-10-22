---
description: Refresh .harness/context.md from recently merged pull requests (via a PR)
allowed-tools: Bash(echo:*)
---

Target repository: !`echo "$HARNESS_REPO"`. Additional focus, if any: $ARGUMENTS

1. Read `.harness/context.md` from the default branch. Treat it as empty if it is missing.
2. List the most recently merged pull requests and read their descriptions. About the last 20 is enough.
3. Write down what durable knowledge they add or change: architectural decisions, conventions, important gotchas. Leave out task-specific detail.
4. If nothing changed, say so and stop.
5. Otherwise, write the updated file on a branch `harness/context-sync-<yyyymmdd>`.
   - Keep the file concise and organised by topic.
   - Remove statements the PRs show are now false.
6. Open a PR titled "Sync harness context". The body should list each change and the PR it came from.
