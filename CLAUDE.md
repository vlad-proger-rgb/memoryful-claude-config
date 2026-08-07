# Memoryful — workspace root

AI-powered life journal. This folder is **not** a git repo; it holds two independent ones:

| Path | What | Repo |
| --- | --- | --- |
| `memoryful-backend/` | FastAPI + async SQLAlchemy + Celery, runs in Docker | own git repo |
| `memoryful-frontend/` | Vue 3 + Vite + Tailwind SPA | own git repo |

Each has its own `CLAUDE.md` with the details — those load automatically when you touch
files inside them. Keep this file to things that span both.

## The local loop

The backend runs entirely in Docker; the frontend runs on the host and proxies to it.

```bash
# 1. backend stack (from memoryful-backend/)
docker compose -p memoryful --env-file .env.local -f docker/docker-compose.local.yml up --build

# 2. frontend (from memoryful-frontend/)
npm run dev
```

Frontend dev server is **:3000**, and `vite.config.ts` proxies the API path prefixes to
`http://localhost:8000`. So the app is at `http://localhost:3000` and there is no CORS
step in local dev.

Ports: app 8000 · mcp 3001 · db 5444 · redis 6379 · minio 9000/9001 · pubsub 8085 ·
ollama 11434.

Local login accepts **any** verification code for the addresses listed in `TRUSTED_EMAILS`
in `memoryful-backend/.env.local` — a development-only bypass, so browser-driven testing
needs no real inbox. Read that variable to get the address; `123123` works as the code.
Restored days reference photos in production GCS, so their images render broken locally;
that's expected.

## Rules

- **Commit only when asked.** Never commit unprompted — I read the whole diff first.
  When I do ask, you write the commit message and commit both repos yourself; don't
  hand the message back for me to paste.
- **Comment only what's genuinely surprising, in one line.** If a decision needs a
  paragraph to defend, refactor until it doesn't. Rationale that belongs in history goes
  in the commit message, not the source.
- **Never *run* anything against production.** No `docker-compose.vm.yml`, no
  `deploy-app.sh`, no `gcloud`/`psql` against Neon. A hook blocks these; do not work
  around it. Local work runs against a *restored copy* of prod data.
- **`.env.prod` is editable config, not a secret.** It holds non-secret production
  settings only — real secrets come from GCP Secret Manager inside the VM at runtime, and
  `deploy-app.sh` just does `cp .env.prod .env` on the box. So a new setting normally lands
  in `.env.local` *and* `.env.prod` in the same pass. Adding one there is expected; only
  deploying it is off limits.
- **Always pass `--env-file .env.local` explicitly.** Compose auto-loads a bare `.env`
  for `${VAR}` interpolation, and that file is host tooling only — it holds a single
  variable, `BACKUP_SOURCE_URL`, the production Neon connection string that
  `manage_backup.py` dumps from. Omitting the flag silently leaves compose-level vars
  empty (classic symptom: Redis `invalid username-password pair`).
- Real secrets live in `.env.local.secrets` — mostly AI provider keys
  (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) and `LLM_MODE`. Gitignored, and `env_file:`
  loads it after `.env.local` so it wins. `.env.local` is committed with placeholders —
  never put a real key there.

## Commit convention

`type(scope): summary` — imperative mood, lowercase after the colon, no trailing period,
subject under ~72 chars. Types: `feat` `fix` `refactor` `perf` `docs` `test` `chore` `build`
`ci`. Scope is the area touched, not the file: `api`, `ai`, `auth`, `db`, `cache`, `mcp`,
`docker`, `deps`, `ui`, `day`, `workspace`.

Body only when the summary genuinely isn't enough. When present it's `- ` bullets, one per
distinct change, explaining *what changed and why* — never a restatement of the diff. No
body at all is the common case and is fine.

```
fix(cache): clear day namespaces when a tag is mutated

refactor(ai): route chat completions through the MCP sidecar
- Replace the direct tool registry with tools loaded from MCP_SERVER_URL
- Drop the duplicated tool schemas that drifted from the server's
```

**One feature, one commit.** That's the default unit — a working, revertable increment.
Don't split a migration away from the model change that motivated it; they ship together or
the tree is broken in between. Only break a feature up when it's genuinely large, and then
split along boundaries that each stand on their own.

What to avoid is the other extreme: a commit that carries a schema redesign, a perf fix, a
refactor and a cleanup at once. If the body needs more than ~6 bullets, or the bullets
describe unrelated concerns, that's two or three features wearing a trenchcoat.

Both repos are committed in the same pass when a change spans them, with messages that
mirror each other so the pair is findable later.

## Cross-repo

- The API contract is hand-maintained on both sides: `app/schemas/` in the backend,
  `src/api/*.ts` + `src/types/` in the frontend. There is no codegen — change one,
  change the other in the same pass.
- Adding a **new top-level API prefix** means editing the proxy regex in
  `memoryful-frontend/vite.config.ts`. Forgetting this is the usual cause of a new
  endpoint 404-ing in dev while working fine in Swagger.
- `memoryful-backend/mcp_server/` is a separate MCP server exposing read-only tools over
  the same API. New read endpoints usually want a tool there too.

## Slash commands

`/stack-up` `/stack-reset` `/logs` `/db-refresh` `/migration` `/verify` — see `.claude/commands/`.
