---
name: capture-task
description: Use when something is worth doing later but not now — the maintainer reports a bug or idea noticed while working on something else, or Claude spots out-of-scope work (dead code, a missing guard, a refactor) during another task. Files it into the Memoryful TickTick board. Also the reference for that board's structure.
allowed-tools: mcp__ticktick__create_task, mcp__ticktick__batch_add_tasks, mcp__ticktick__list_projects, mcp__ticktick__get_project_with_undone_tasks, mcp__ticktick__search_task, mcp__ticktick__list_tags, Read, Grep, Glob
---

# Capturing a task

TickTick is the single source of truth for what to build. Nothing is created in GitHub at
capture time — see *Why no GitHub issue yet* below.

## Board reference

Project **Memoryful** — `67076bd2657043bee4ed683a`

| Column | id | For |
|---|---|---|
| Backlog | `67076be4657043bee4ed685f` | Someday-maybe: integrations, big speculative features |
| General | `67601a0b6570db0e3969a4a4` | Cross-cutting, product-level, or spans both repos |
| FastAPI BE | `67c357f6ebbd7d0000000389` | Backend work |
| Vue.js FE | `67c35918ebbd7d0000000392` | Frontend work |
| Admin Dashboard | `69c64fa4657062cfd9f384a4` | The admin/analytics surface — not built yet, shape undecided |
| **Claude Backlog** | `6a71069d8f08cc64fe195c59` | **Everything Claude files. Triage queue, see below** |

Pick by *where the work happens*, not by who noticed it. Backlog is for things with no
intent to start soon — don't park real bugs there.

**Priority**: `0` none · `1` low · `3` medium · `5` high. Not 1-4. Default `0` unless
there's a reason.

**Tags** — use the lowercase slug, not the display label:
`auth` `cleanup` `deployment` `extensions` `memoryfulai` `mobile` `mvp` `newfeature`
`organization` `over-engineering` `post-release` `refactor` `research` `security`
`subscription` `tests` `ui` `claude`

`mobile` collects the phone/tablet support effort — anything that only misbehaves at a
narrow width, on touch, or inside the planned store wrapper. It is being actively filled,
so add it to any finding of that shape even when another tag also applies.

`auth` collects everything touching how someone gets in and stays in — login, sessions,
tokens, the users table, account linking. Added 2026-08-21 because that surface ends up
being a large share of the code and had no way to be seen as one thing.

Two tags on this board belong to other projects and must never be used here: `discuss`
(cross-team discussion elsewhere) and `jobhunt`. Use existing tags only — if none fit, say
so and ask rather than inventing one.

## The two flows

### The maintainer reports it — usually via `/task`

Goes straight into the right working column, normally. The report is the symptom; do the
research yourself before writing — grep for the relevant code, confirm the behavior, and
put what you find in the body.

### Claude noticed it mid-task

Everything Claude files goes to the **Claude Backlog** column with the **`claude` tag**,
plus whatever topical tags apply. It's a triage queue: findings land there, get verified,
and get moved into a working column by hand.

That scope is enforced, not just conventional — `.claude/hooks/ticktick_scope.py`
auto-approves creation only when every task is addressed to that column *and* carries the
`claude` tag. Anything aimed elsewhere still prompts. So:

1. Finish the task at hand first. Don't derail mid-change.
2. File into Claude Backlog with the `claude` tag. No confirmation needed — that's the
   point of the column existing.
3. **Say which column it should end up in**, as the last line of the body:
   `Suggested column: FastAPI BE`. That's the hand-off; don't make the reader guess.
   It belongs only on tasks sitting in Claude Backlog awaiting triage — a task already
   filed in a working column is where it belongs, and the line is noise there.
4. Batch several findings into one `batch_add_tasks` call.

The `claude` tag stays on the task after it's moved out, so provenance survives triage.

Writing into any *working* column still needs a yes, however confident the finding.

## Writing the task

`title` — what needs to happen, not what's wrong. "Redirect unauthenticated users to login"
beats "auth is broken". Fits on one kanban card.

`content` — what makes it actionable in six months, when the context is gone:

- What was observed, and how to reproduce it
- Where in the code it lives
- Why it matters, if not obvious
- Anything already ruled out

**Anchor on code, not line numbers.** `auth.py:120` is wrong the moment anything above it
shifts. Name the file and the symbol, and quote the couple of lines that matter:

> In `app/routers/auth.py`, `verify_code`:
> ```
> if code_form.email not in TRUSTED_EMAILS:
> ```

That stays findable with a grep after the file has moved on, and it shows the reader exactly
what you saw. Same for a function that's been renamed — the quoted line still finds it.

## Before creating

`search_task` on a keyword from the title. This board has ~30 open items going back to early
2025, so duplicates are easy. If a near-match exists, surface it and ask whether to extend
that one instead of adding another.

## Why no GitHub issue yet

Most captured ideas are never built, and an issue created at capture time is a coin flip on
ever being closed — 30 open TickTick items would mean 30 stale issues and two places to
close each. The GitHub issue earns its keep only when work actually starts and a commit can
say `resolves #N`. That's a separate step, deliberately not part of capture.
