---
description: Autogenerate an Alembic revision from model changes, review it, then apply by restarting the app
argument-hint: <short_snake_case_name>
allowed-tools: Bash(docker:*), Read, Edit, Grep, Glob
---

Model changes in the working tree:

!`cd memoryful-backend && git diff --stat app/models/`

Current revision state:

!`docker exec memoryful-app-local alembic current 2>&1 | tail -5`

Create a revision named: `$ARGUMENTS`

Take the first whitespace-delimited token as the name and ignore any commentary after it.
**Don't use `$1`** — it has come through unsubstituted on this command, which would name the
revision literally `$1`. `$ARGUMENTS` is reliable.

**If the model diff above is empty, say so before generating.** Autogenerate still produces
a valid revision, just with `pass` in both directions. That's fine as a test but it is not
free — see cleanup below.

**How applying works here:** the app container's compose `command:` is
`alembic upgrade head && uvicorn ... --reload`. That chain runs *once per container start*.
Uvicorn's `--reload` restarts only the Python process on file change, so a freshly generated
revision is **not** picked up by hot-reload — the container has to restart. That is the only
step that applies migrations; never run `alembic upgrade head` by hand.

Steps:

1. Autogenerate inside the container so the URL and driver match:

   ```bash
   docker exec memoryful-app-local alembic revision --autogenerate -m "<name>"
   ```

   The engine runs with `echo=True`, so this buries the result under hundreds of lines of
   `pg_catalog` reflection SQL. Filtering on `sqlalchemy.engine` isn't enough — the wrapped
   continuation lines carry no logger prefix. Just take the tail and look for the one line
   that matters: `Generating /app/alembic/versions/<rev>_<name>.py ...  done`.

2. **Read the generated file before anything else.** Confirm it matches the model diff above
   and contains nothing I didn't ask for. Alembic cannot detect renames — it emits them as
   drop + add, which silently destroys the column's data.
3. Hand it to the `migration-reviewer` subagent. Stop and show me its findings if anything
   comes back at severity 1 or 2.
4. Once I approve, apply it by restarting the app:

   ```bash
   docker compose -p memoryful --env-file .env.local -f docker/docker-compose.local.yml restart app
   ```

5. Confirm it took: `docker exec memoryful-app-local alembic current` should show the new
   revision, and `docker logs memoryful-app-local --tail 30` should show uvicorn started.
   If the migration fails, `&&` stops the chain and uvicorn never starts — the container will
   be down with the Alembic traceback in its logs. That's the signal to look for, not a 500.
6. Run `docker exec memoryful-app-local mypy` and report.

Never hand-edit a file in `alembic/versions/` — generate a new revision instead.

## Discarding a revision

If the revision turns out to be unwanted (a test run, or autogenerate produced something
wrong), **delete the file before restarting the app — never after.**

Order matters and the failure is not obvious. Restarting applies it, which writes the new id
into `alembic_version`. Delete the file at that point and the DB references a revision that
no longer exists on disk, so every subsequent `alembic` command fails with
`Can't locate revision identified by '<id>'` — including the `upgrade head` in the container's
start command, which means the app won't boot.

- **Not yet restarted:** just `rm` the file. Confirm with `alembic current` that the DB is
  still on the previous head first.
- **Already restarted:** `alembic downgrade -1` first, verify `alembic current` moved back,
  then delete the file.
