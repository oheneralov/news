+# Claude Code harness

In this variant, Claude Code itself is the agent loop, so there is no application code.
GitHub is still the system of record, reached only through the official GitHub MCP server.

| File | Purpose |
| --- | --- |
| `.mcp.json` | Remote GitHub MCP server. The PAT comes from `${GITHUB_PAT}`, so no secret is committed. |
| `CLAUDE.md` | The workflow and the rules the agent follows. |
| `.claude/settings.json` | Permission rules:<br>- reads are allowed<br>- writes ask first<br>- merge and delete are denied<br>It also registers the policy hook. |
| `.claude/hooks/guard_branch.py` | PreToolUse hook. Restricts calls to `HARNESS_REPO` only, limits writes to `harness/*` branches, and allows label-only issue updates. It mirrors `harness_core.guard`. |
| `.claude/commands/` | `/next-task`, `/ship <issue>`, `/sync-context` |

## GitHub PAT

The GitHub MCP server authenticates with a Personal Access Token (PAT): a password-like token
that lets a program act on GitHub as you, limited to the repositories and permissions you grant.

To create one:
1. On GitHub, open **Settings → Developer settings → Personal access tokens → Fine-grained tokens**
   (https://github.com/settings/personal-access-tokens) and choose **Generate new token**.
2. Set a name (for example `claude-code-harness`) and an expiration.
3. Under **Repository access**, select only the target repository (`HARNESS_REPO`).
4. Under **Repository permissions**, grant **Read and write** for **Contents**, **Issues**, and
   **Pull requests**. **Metadata: Read** is added automatically.
5. Generate the token and copy it right away. GitHub shows it only once (it starts with `github_pat_`).



Treat the token like a password. Keep it in the `GITHUB_PAT` environment variable
Option 3: current terminal only (temporary)
$env:GITHUB_PAT = 'github_pat_xxxxxxxx'
$env:HARNESS_REPO = 'owner/name'
cd C:\alex\work\spok\claude-code-harness
claude
, never in
`.mcp.json` or any committed file. If it leaks, revoke it on the same GitHub page.

## Use

```bash
export GITHUB_PAT=...           # the fine-grained PAT from above
export HARNESS_REPO=oheneralov/new
cd claude-code-harness
claude
```

On Windows (PowerShell), set them persistently for your user and then restart your terminal or VS Code:

```powershell
[Environment]::SetEnvironmentVariable('GITHUB_PAT', 'github_pat_xxxxxxxx', 'User')
[Environment]::SetEnvironmentVariable('HARNESS_REPO', 'oheneralov/news', 'User')
```

Start Claude Code from the `claude-code-harness` directory. `.mcp.json` is read only from the
project root, so the `github` server does not load if you start Claude Code from a parent directory.

Inside Claude Code:
1. Run `/mcp` and check that `github` is connected.
2. Run `/next-task`. Claude picks the oldest `ai-task` issue and proposes a plan.
3. Run `/ship <issue>`. Claude creates the branch, commits, opens the PR, and comments and relabels the issue.
4. Run `/sync-context` from time to time. Claude refreshes `.harness/context.md` from merged PRs, as a PR.

The hook runs with `python` from your `PATH` and needs only the standard library.
It fails closed: if `HARNESS_REPO` is unset, every GitHub MCP call is blocked.

## Usage

### How changes reach GitHub

There is no local clone and no `git push`. Claude writes to GitHub through the `github` MCP tools,
and each write is a commit made directly on GitHub:

| Step | MCP tool | What happens on GitHub |
| --- | --- | --- |
| Create branch | `create_branch` | `harness/<issue>-<slug>` is created from the default branch. |
| Commit one file | `create_or_update_file` | One commit on the harness branch. |
| Commit several files | `push_files` | One commit with all files on the harness branch. This is the "push". |
| Open PR | `create_pull_request` | PR from the harness branch into the default branch. |
| Report | `add_issue_comment`, `issue_write` | Comment on the issue, and relabel `ai-task` → `ai-in-review` (or `ai-failed`). |

Every write tool is in the `ask` list, so Claude Code asks you to approve each call. The hook
blocks writes to any branch that does not start with `harness/` (override with
`HARNESS_BRANCH_PREFIX`), and the deny rules block merging and deleting. A human merges the PR.

### Example 1: ship an issue end to end

1. Create a task in the target repository. Use the web UI, or the `gh` CLI:

   ```bash
   gh issue create --repo "$HARNESS_REPO" \
     --title "Add /health endpoint" \
     --body "Return 200 with {\"status\": \"ok\"}. Add a test." \
     --label ai-task
   ```

2. Start Claude Code in this directory and ask for a plan:

   ```text
   > /next-task
   ```

   Claude picks the oldest open `ai-task` issue (or the one you name, for example `/next-task 12`),
   reads `.harness/context.md`, `AGENTS.md`, `CLAUDE.md` and the relevant files, and replies with a plan:

   ```text
   Issue #12: Add /health endpoint
   Branch: harness/12-add-health-endpoint
   Files:
     - app/api/routes/health.py: new router returning {"status": "ok"}
     - app/main.py: include the router
     - tests/api/test_health.py: API test
   Open questions: none
   ```

3. Ask for changes to the plan in plain language if needed, for example
   `Also document the endpoint in README.md`. Nothing has been written to GitHub yet.

4. Ship it:

   ```text
   > /ship 12
   ```

   Approve each write prompt as it appears: the start comment, `create_branch`, `push_files`,
   `create_pull_request`, the finish comment, and the label change.

5. Review the PR on GitHub (or with `gh pr view --repo "$HARNESS_REPO" --web`) and merge it yourself.

### Example 2: push follow-up changes to an open PR

The PR branch is an ordinary `harness/*` branch, so later commits land on the same PR.
In the same session, or a new one, ask for the change directly:

```text
> The review on PR #13 asks to return the app version from /health too.
  Read the review comments, update harness/12-add-health-endpoint with push_files,
  and reply on the PR with a summary.
```

### Example 3: push an ad-hoc change without an issue

You can ask for a change without an issue, as long as it goes through a `harness/` branch and a PR:

```text
> Fix the typo "recieve" in docs/setup.md. Commit it on a new branch
  harness/fix-setup-typo and open a PR into the default branch.
```

If you ask Claude to commit to `main` (or any non-`harness/` branch), the hook blocks the call with
`Writes are only allowed on branches starting with 'harness/'.`

### Example 4: refresh the shared context

```text
> /sync-context
> /sync-context focus on testing conventions
```

Claude reads the last ~20 merged PRs and, if `.harness/context.md` needs updating, pushes it to
`harness/context-sync-<yyyymmdd>` and opens a PR titled "Sync harness context".

### Example 5: run without the interactive UI

Print mode cannot answer approval prompts, so pre-approve the write tools for that run only:

```bash
claude -p "/ship 12" --allowedTools \
  "mcp__github__create_branch,mcp__github__push_files,mcp__github__create_or_update_file,mcp__github__create_pull_request,mcp__github__add_issue_comment,mcp__github__issue_write"
```

The hook and the deny rules still apply. Without a plan from an earlier turn, `/ship` runs the
`/next-task` steps first and then implements its own plan, so prefer the interactive flow for
anything non-trivial.

### Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `/mcp` shows no `github` server | Claude Code was started outside `claude-code-harness`. Restart it from this directory. |
| `HARNESS_REPO (owner/name) must be set` | Set `HARNESS_REPO` and restart the terminal or VS Code. |
| `Only owner/name may be accessed` | Claude targeted another repository. Check `HARNESS_REPO`. |
| `Search queries must include 'repo:owner/name'` | Ask Claude to scope the search to the target repository. |
| 401 / 403 from GitHub | The PAT is missing, expired, or lacks Contents, Issues, or Pull requests write access. |

