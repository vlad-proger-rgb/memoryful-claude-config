---
name: ship-task
description: Use when the maintainer hands over a TickTick task to actually build — a pasted ticktick.com task link, a task id, or "implement/fix this one". Covers the full lifecycle from pulling the task through committing on dev and writing the completion comment. Not for capturing new tasks (that is capture-task) and not for ad-hoc changes with no task behind them.
---

# Shipping a task

The order below exists because the rules that matter fire *early* — branch, scope, plan —
and are unrecoverable once momentum builds. A commit on `main` or an hour spent on the wrong
design are both cheap to prevent at step 0 and expensive at step 8.

Two steps are **blocking**: 3 and 7. Everything else runs without asking.

## 0. Branch

`memoryful-backend` and `memoryful-frontend` both work on `dev`. Check every repo the change
will touch, before writing anything:

```bash
git -C memoryful-backend branch --show-current
```

Not on `dev`? Stop and ask — switching may mean stashing, and that is the maintainer's call.
The workspace-root repo is the exception: it only has `main`, and workspace tooling commits
there normally.

## 1. Pull the task

A board URL is `…/#p/<projectId>/tasks/<taskId>` — both halves go to
`mcp__ticktick__get_task_in_project`. Given only a bare id, `get_task_by_id` works.

Then `mcp__ticktick__get_comment` on the same pair. **Always.** Comments are where finished
work and corrections get written on this board, so the body alone can be stale or already
answered — an earlier comment may say the thing was fixed, or that the body's diagnosis was
wrong.

## 2. Confirm it is still live

Read the body as a *symptom report*, not a spec. Find the code it names, reproduce the
behavior, and confirm the problem still exists on `dev` today.

Three outcomes:

- **Still broken** — carry on to step 3.
- **Already fixed** — say so, point at the commit or code that fixed it, and ask before
  completing the task. Don't silently close it.
- **The body is wrong** — the described cause doesn't hold, or the real problem is
  elsewhere. Say so before planning. The correction goes in a *comment* at step 9, never
  over the body; the body is the brief, and rewriting it destroys what made the task worth
  keeping.

## 3. Plan — blocking

**At most 8 lines**, three things only:

- which files change
- what changes in each, in a phrase
- what will prove it works

No prose rationale, no alternatives considered, no restating the task back. The maintainer
is reading this to catch a wrong approach in ten seconds, not to be educated.

Then **stop and wait for a yes.** This is a real gate — implementing through it is the
single most expensive mistake available here.

If the task turns out to be two or three unrelated features, say so at this point and
propose the split. That decision belongs to the maintainer, before any code exists.

## 4. Implement

The mechanics live elsewhere and are not repeated here — use them:

| Work | Where |
|---|---|
| API route, schema, cache namespaces, vite proxy, MCP mirror | `backend-endpoint` skill |
| Model change → Alembic revision | `/migration` |
| Something out of scope noticed on the way | `capture-task` skill |

That last row is the scope valve, and it matters. A finding filed into Claude Backlog costs
nothing and survives; the same finding fixed inline turns a reviewable diff into a mixed one
the maintainer has to untangle. Finish the task at hand.

## 5. Prove it

Mechanical checks: run `/verify` and report what it says. Fix what the change broke; a
failure that predates the change gets reported, not silently fixed.

**`xfail` markers are `strict=True` here.** Three tests are marked (in `test_days.py`,
`test_months.py`, `test_workspaces.py`) and strict mode turns an unexpected *pass* into a
failure. So fixing one of those bugs makes the suite go red until the marker comes off —
removing it is part of the fix, not an afterthought.

Then exercise the actual path in the browser preview, **at 1280 and at 375**. Mobile is a
first-class target here, not a follow-up; anything that only misbehaves narrow is a real
defect, not a polish item.

Report pass/fail with the output. Never "should work" — either it was exercised or it wasn't,
and saying which is the whole value of this step.

## 6. Self-review the diff

Read the full diff before the maintainer does, and cut:

- **Comments that restate the line below them.** `# print the error` above a `logger.error`
  is noise. Keep a comment only when it says something the code cannot.
- **Comments narrating the change** — "now we also handle X". The diff already shows that.
- **Comments explaining why the old code was wrong.** That is the TickTick comment's job,
  step 9.
- Anything nobody asked for: drive-by renames, reformatting outside the change,
  "while I was here" edits.

The rule of thumb for the whole handoff: **the commit says what changed, the TickTick comment
says why it broke and what to watch.** Applied here, it keeps both short later.

## 7. Hand over — blocking

Say what changed and what was verified, in a few lines. Then wait.

The maintainer reviews the diff and tests on a real phone, which catches things the embedded
browser does not. Feedback comes back to **step 4** — fix and re-verify. Don't re-plan and
don't re-litigate the approach; it was already agreed at step 3.

## 8. Commit

Only after an explicit yes. Write the message and commit — never hand a message back to be
pasted.

Follow the convention in the root `CLAUDE.md`: `type(scope): summary`, imperative, no body in
the common case. **No diagnosis in the message.** Why it broke, what was ruled out, what
surprised you — none of that belongs here. It goes in step 9, which has room for it.

A change spanning both repos commits in the same pass, with mirrored messages.

## 9. Comment on the task

`mcp__ticktick__add_comment`, with the short sha first — that is the only link between the
board and the history, so it leads:

```
a8745db — <what changed, a line or two>

<what would bite the next person, if anything>
```

Two repos means both shas, labeled.

Keep it to a few lines. The diff holds the detail; this holds what the diff can't say. Don't
write "not pushed yet" or any other state claim — it is wrong within the day and nobody
returns to correct it.

The 1024-character cap truncates **silently**. It is a backstop, not a target: a comment
trimmed to fit was already too long.

## 10. Complete the task

`mcp__ticktick__complete_task`. Last, and only after the comment exists — a task closed with
no write-up is the one nobody can reconstruct later.
