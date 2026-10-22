---
name: git-push-all
description: Stage all local changes, commit them, and push the current branch in one step
argument-hint: "[commit message]"
disable-model-invocation: true
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(git rev-parse:*), Bash(git branch:*)
---

Commit message, if one was given: $ARGUMENTS

This works on the local checkout in the current directory. It is not part of the MCP flow, which never pushes from a local clone.

1. Run `git status --porcelain`. If it prints nothing, say there is nothing to commit and stop.
2. List the files that will be staged. Point out any that look like secrets or credentials (for example `.env`, `*.pem`, `*.key`, files with `secret` or `token` in the name) and ask before going on if there are any.
3. Get the current branch with `git rev-parse --abbrev-ref HEAD`. If it is `main` or `master`, ask before going on.
4. Run `git add -A`.
5. Commit with `git commit -m "<message>"`.
   - Use the message given above if there is one.
   - Otherwise read `git diff --cached` and write a short, imperative summary of the change.
6. Push with `git push`. If the branch has no upstream yet, use `git push -u origin <branch>` instead.
7. Report the commit SHA, the branch, and the remote it was pushed to.

Never pass `--no-verify`, `--force` or `--force-with-lease`. If a hook, the commit or the push fails, report the error and stop.
