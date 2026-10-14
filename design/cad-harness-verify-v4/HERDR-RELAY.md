# herdr + omp relay (migration 2026-10-14 JST)

## Setup
- Migrated from Orca. The user authorized operating herdr from outside HERDR_ENV at 11:57 JST.
- Existing workspace w5 (C:\dev\CAD-HARNESS; panes w5:p1 codex and w5:p2 omp) is NOT touched.
- Own workspace w6, label "CAD-HARNESS-v4". It is a linked git worktree at `C:\dev\CAD-HARNESS-herdr` on branch `herdr/v4` (base proto/cad-run 159b655).
- Agents (omp v18.10.4, interactive):

| Agent | Pane | Model |
|---|---|---|
| v4codex | w6:p1 | openai-codex/gpt-6.1-sol |
| v4grok | w6:p2 | opencode-go/grok-4.7 |
| v4gemini | w6:p3 | google-antigravity/gemini-3.8-flash |

- Each agent answered a real PONG prompt sent through herdr.

## Commands (PowerShell on DPC-019)
```
$h='C:\Users\backo\AppData\Local\Programs\Herdr\bin\herdr.exe'
& $h agent list
& $h agent prompt v4codex "<text>" --wait --timeout 900000
& $h agent read v4codex --source recent-unwrapped --lines 120
& $h agent get v4grok            # status: idle | working | blocked | done
& $h agent send-keys v4gemini esc
```
- If a prompt returns blocked, inspect it with `agent read` before answering. Never blindly re-send after a timeout.
- Long answers: ask the agent to write a file under design\cad-harness-verify-v4\ and reply with the path only.

## Non-interactive omp
```
omp -p --no-session --model <m> --cwd <dir> "<prompt>"
```
Stdin MUST be closed or redirected (for example `-RedirectStandardInput $env:SystemRoot\win.ini` with Start-Process). Otherwise it hangs.

## Usage and quota
`omp usage` lists all accounts. Codex 7-day usage was 10.0% at migration time.

## Git
- Commit in `C:\dev\CAD-HARNESS-herdr` on herdr/v4.
- Push as a fast-forward only: `git push origin herdr/v4:proto/cad-run`. No force. No reports/ or .tmp/.
- The worktree has no untracked v3 `reports/`. Read historical reports from C:\dev\CAD-HARNESS\reports, read-only.

## herdr in-pane-only rule (official skill, `herdr --skill`)
- The skill says: verify HERDR_ENV=1 before any control command. Otherwise "do not inspect or control the focused Herdr session from outside Herdr".
- Stated reasons:
  - Inside a pane, the `herdr` binary talks to *the current session*, and Herdr injects the caller's workspace, tab and pane IDs, so `--current` targets the right pane.
  - From outside, commands may resolve to "the UI-focused pane, which can belong to the user or another client".
  - The rule therefore prevents acting on someone else's panes or session.
- Mitigation used here: explicit pane IDs and agent names only, never `--current` or the focused pane, a separate workspace and worktree, and `--no-focus`.

## USER 2026-10-14 22:08 JST - Grok effort
- Grok always runs at High effort. v4grok stays on native Grok Build, model grok-4.7, effort high, on every restart (launch: grok -m grok-4.7 --cwd C:\dev\CAD-HARNESS-herdr in w8:p2; confirm the footer shows "Grok 4.7 (high)").
