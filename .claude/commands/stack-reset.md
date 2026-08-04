---
description: Tear down the local stack including volumes, then rebuild from a fresh DB dump
allowed-tools: Bash(docker:*), Bash(curl http://localhost:*), Read
---

**Destructive**, but usually cheaper than it sounds — measured end to end at roughly one
minute. `down -v` deletes four volumes: `postgres_data_local`, `minio_data_local`,
`redis_data_local`, `ollama_data_local`. Three of them re-seed themselves on the next `up`:

- **Postgres** — `docker/init-restore-db.sh` reloads `backups/neondb_backup_latest.dump`.
  It only runs when the volume is empty, which is exactly the case after `down -v`. If the
  dump is missing it logs and starts empty rather than failing, so this can't wedge.
- **MinIO** — `minio-init` re-mirrors `bucket_base/` (~6 MiB).
- **Redis** — cache only, nothing to recover.

Before doing anything:

1. Report the dump's date and size. **Use PowerShell `Get-ChildItem`, not `ls`** — `backups/`
   is in the `Read` deny list and a Bash listing of it gets refused, and Glob won't show it
   either since the directory is gitignored. If the dump is missing or stale, stop and say
   so — `/db-refresh` may be wanted first.
2. **Check `docker exec memoryful-ollama-local ollama list` before warning about Ollama.**
   Nothing is normally installed — AI runs through Vertex/LangChain, not local Ollama — so
   there is usually no ~4.7 GB re-pull to worry about. Only raise it if a model is actually
   listed. Don't quote a cost that isn't being paid.
3. Show exactly what will be destroyed and wait for an explicit go-ahead.

After I confirm:

```bash
cd memoryful-backend && docker compose -p memoryful --env-file .env.local -f docker/docker-compose.local.yml down -v
cd memoryful-backend && docker compose -p memoryful --env-file .env.local -f docker/docker-compose.local.yml up --build -d
```

Then verify, in this order:

1. `docker logs memoryful-db-local | grep "\[init-restore\]"` — expect `Restoring ... Done.`
2. Health-check `http://localhost:8000/`.
3. `docker exec memoryful-app-local alembic current` — the dump carries prod's
   `alembic_version`, so **0 upgrades applied is the correct outcome** when prod is current.
   Migrations running here means prod is behind head, which is worth mentioning.
4. Confirm the data actually returned — authenticate and check a couple of endpoints, don't
   just trust that the container started.

Only if step 2 of the pre-flight found an installed model, remind me to re-pull it:

```bash
docker exec -it memoryful-ollama-local ollama pull llama3.1
```
