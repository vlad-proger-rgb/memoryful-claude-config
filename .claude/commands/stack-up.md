---
description: Start the local backend stack and report which services came up healthy
argument-hint: [service ...]
allowed-tools: Bash(docker:*), Bash(curl http://localhost:*)
---

Already running:

!`docker ps --filter name=memoryful --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"`

Start the local stack (non-destructive — volumes and DB data survive). Services: `$ARGUMENTS`
(empty means all).

```bash
cd memoryful-backend && docker compose -p memoryful --env-file .env.local -f docker/docker-compose.local.yml up --build -d $ARGUMENTS
```

Then:

1. Wait for containers to settle, re-run `docker ps --filter name=memoryful`.
2. Health-check the API: `curl -s http://localhost:8000/` should return
   `{"code":200,"msg":"Memoryful is running!"}`.
3. For any container not in a running state, pull its last 40 log lines and diagnose —
   **except `memoryful-minio-init`, which is a one-shot seeder and is *supposed* to exit.**
   It mirrors `bucket_base/` into the local MinIO bucket and stops; `Exited (0)` with
   `minio seed complete` in its log is success, not a failure to report.
4. The `app` container runs `alembic upgrade head` before uvicorn. If it's down, check its
   logs for an Alembic error before assuming anything else — a failed migration stops the
   chain and uvicorn never starts.
5. Report a one-line-per-service status table. Do not start the frontend — that is `/verify`
   or a separate `npm run dev`.
