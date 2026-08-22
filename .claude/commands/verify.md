---
description: Run every check across both repos and report what's broken
allowed-tools: Bash(docker:*), Bash(ruff:*), Bash(npm run:*), Bash(npx:*), Bash(curl http://localhost:*), Read
---

Run all of these, keep going after failures, then report one consolidated list.

The backend block mirrors the four jobs CI runs — `ruff`, `mypy`, `test (app)`,
`test (mcp_server)` — so that green here means green there. That equivalence is the whole
point of this command: anything added to the workflow belongs here too, or `/verify` starts
quietly meaning "most of CI".

**Backend** (`memoryful-backend/`)
- `ruff check .` — lint.
- `ruff format --check .` — formatting, and it does **not** stop at `.py`: ruff formats
  python code blocks inside **markdown**, so a snippet in `specs/` fails this exactly as a
  source file would. Use `--check`, which only reports; bare `ruff format` rewrites the tree
  and a verification pass must not do that.
- `docker exec memoryful-app-local mypy` — strict mode: `disallow_untyped_defs`,
  `warn_return_any`, `warn_unreachable` are all on. Covers `app` and `mcp_server`.
- `docker exec memoryful-app-local pytest app/tests` — the core suite. Three tests are
  marked `xfail(strict=True)`, so an unexpected *pass* counts as a failure: it means a known
  bug got fixed and its marker needs removing as part of that fix.
- `docker exec memoryful-mcp-local pytest mcp_server/tests` — **the path is required.**
  Bare `pytest` also collects `app/tests`, which imports settings and needs the DB and the
  full environment the mcp container deliberately does not carry, so it dies at collection
  with a `SettingsError`. That is the command being wrong, not the container being broken.
- `curl -s http://localhost:8000/` — API alive.

**Frontend** (`memoryful-frontend/`)
- `npm run type-check` — `vue-tsc --build`
- `npx eslint .` — **not** `npm run lint`, which is `eslint . --fix` and rewrites source
  files. A verification pass must not mutate the working tree; if it did, the diff you
  review afterwards would include changes nobody asked for.
- `npm run test:unit -- --run --passWithNoTests` — vitest, non-watch. There are currently
  **no unit tests** in this repo (`src/components/__tests__/` is an empty leftover from the
  Vue starter). Without the flag, vitest exits 1 on "No test files found", which is absence
  of coverage, not a failure. Report it as "no tests" — never as a failing check.

Report format: one line per check with pass/fail, then the details of each failure with the
file and line. Fix nothing unless I ask. If a check can't run because a container is down,
say so rather than reporting it as a failure.
