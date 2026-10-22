---
name: harness-ship
description: Implement the agreed plan on a harness branch, open a PR, and report on the issue
argument-hint: "<issue>"
disable-model-invocation: true
allowed-tools: Bash(echo:*)
---

Issue: $ARGUMENTS. Target repository: !`echo "$HARNESS_REPO"`

Follow the plan agreed in this conversation. If there is no plan yet, run the `/harness-next-task` steps first.

1. Comment on the issue: "Harness picked up this issue. Working on branch `<branch>`."
2. Create the branch `harness/<issue>-<slug>` from the default branch.
3. Commit the changes to that branch. Use `push_files` when you change several files.
   - If you learned something durable, update `.harness/context.md` in the same commit.
4. Open a pull request from that branch into the default branch.
   - The PR body must include `Closes #<issue>`, a summary of the changes, and how to verify them.
5. Comment on the issue with the PR link and a short summary.
6. Update the issue's labels: replace `ai-task` with `ai-in-review`, and keep the other labels.

If any step fails, comment on the issue with what failed. Then replace `ai-task` with `ai-failed` and stop. Never retry a call that the harness hook blocked.
