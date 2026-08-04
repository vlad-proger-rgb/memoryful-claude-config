---
description: Run every check across both repos and report what's broken
allowed-tools: Bash(docker:*), Bash(mypy:*), Bash(npm run:*), Bash(curl http://localhost:*), Read
---

Run all of these, keep going after failures, then report one consolidated list:

**Backend** (`memoryful-backend/`)
- `docker exec memoryful-app-local mypy` — strict mode: `disallow_untyped_defs`,
  `warn_return_any`, `warn_unreachable` are all on. Covers `app` and `mcp_server`.
- `docker exec memoryful-mcp-local pytest` — the MCP server's tests.
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
