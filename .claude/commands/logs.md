---
description: Pull and diagnose logs from a local container
argument-hint: <service> [lines]
allowed-tools: Bash(docker:*), Read, Grep
---

Containers:

!`docker ps -a --filter name=memoryful --format "{{.Names}}\t{{.Status}}"`

Service: `$1` — accepts either the compose service name (`app`, `mcp`, `db`, `celery`,
`redis`, `rabbitmq`, `flower`, `minio`, `ollama`) or the full container name like
`memoryful-app-local`. Line count: `$2`.

**If `$1` came through empty**, I invoked this bare. Default to `app` and say so — don't
stop to ask. If `$2` is empty, use 100. (Only `$1`/`$2`/`$ARGUMENTS` get substituted here;
shell default syntax like `${2:-100}` is passed through literally, so it can't be used.)

Then:

- **Filter the SQL echo before reading `app` or `celery` logs.** The engine runs with
  `echo=True`, so roughly 60% of lines are SQLAlchemy statements and bound parameters —
  measured at 172 of 289 lines on an idle container. A raw `--tail 100` is mostly noise
  and can push the actual event out of view. Strip it first:
  ```bash
  docker logs memoryful-app-local --tail 200 2>&1 | grep -v "sqlalchemy.engine.Engine"
  ```
  Then take the tail of what's left. Search the *unfiltered* log when hunting a specific
  query, since that's the one case the noise is the point.
- Summarize what happened, newest first.
- For each traceback or ERROR line, open the referenced source file and explain the actual
  cause. Don't just restate the log.
- If it's a startup failure, check the usual suspects in order: an Alembic error (the app's
  compose command is `alembic upgrade head && uvicorn ...`, so a bad migration means uvicorn
  never starts), missing `--env-file .env.local`, or a `.env.local.secrets` value that
  overrode a placeholder with an empty string.
- `memoryful-minio-init` is a one-shot seeder — `Exited (0)` after `minio seed complete` is
  correct, not a fault.
- Propose a fix. Do not apply it unless I ask.
