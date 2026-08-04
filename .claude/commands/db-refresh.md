---
description: Dump production data and restore it into the running local database
allowed-tools: Bash(docker:*), Bash(python scripts/python/manage_backup.py:*), Read
---

Refresh local data from prod. This is **read-only against production** — it dumps, it never
writes. Nothing here may modify the Neon database.

Check existing dumps with the **Glob** tool on `memoryful-backend/backups/*`, not a shell
`ls`. `backups/` is in the `Read` deny list, and a Bash listing of it gets refused by the
permission layer — which aborts this whole command before it starts. Glob returns nothing
for that directory anyway (it's gitignored), so treat "no results" as inconclusive rather
than as "no dump exists"; step 2 verifies existence properly.

Steps, from `memoryful-backend/`:

1. `python scripts/python/manage_backup.py backup` — dumps prod to
   `backups/neondb_backup_latest.dump` plus a timestamped copy. Postgres client tools run
   inside a Docker image, so nothing needs to be installed on the host.
2. `python scripts/python/manage_backup.py restore` — loads it into the **already-running**
   local `db` container, no volume wipe.
3. Verify: the `app` container still answers on `http://localhost:8000/`, and report the
   row count of a couple of core tables so I can see the data actually landed.

**Run both steps with `PYTHONUTF8=1`.** `manage_backup.py` prints `✓` on success, and this
console is cp1251 — so the script dies with `UnicodeEncodeError` *after* the work is already
done. Without the flag, `backup` looks like it failed while having produced a perfectly good
dump. Don't re-run it on seeing that traceback; check whether the dump exists first.

Notes: this needs `BACKUP_SOURCE_URL` in `memoryful-backend/.env` (host-only, never loaded
into a container). If the dump's Postgres major doesn't match the local `db` image, the
restore fails — both must stay on **18**, set in `manage_backup.py` (`PG_IMAGE`) and
`docker/docker-compose.local.yml`. Photos are not mirrored; restored days with photos will
show broken image links locally, which is expected.
