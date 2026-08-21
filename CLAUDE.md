# Memoryful — workspace root

AI-powered life journal. Three independent git repos, and **this folder is one of them** —
it versions only the workspace tooling (`.claude/`, `.mcp.json`, `.vscode/`, this file).

| Path | What | Repo |
| --- | --- | --- |
| `memoryful-backend/` | FastAPI + async SQLAlchemy + Celery, runs in Docker | own git repo |
| `memoryful-frontend/` | Vue 3 + Vite + Tailwind SPA | own git repo |

Each has its own `CLAUDE.md`, loaded when you touch files inside it. Keep this file to
things that span both.

## The local loop

Backend runs in Docker; frontend runs on the host and proxies to it.

```bash
# 1. backend stack (from memoryful-backend/)
docker compose -p memoryful --env-file .env.local -f docker/docker-compose.local.yml up --build

# 2. frontend (from memoryful-frontend/)
npm run dev
```

The app is at `http://localhost:3000`, which proxies the API prefixes to `:8000` — so no
CORS step locally. Ports: app 8000 · mcp 3001 · db 5444 · redis 6379 · minio 9000/9001 ·
pubsub 8085 · ollama 11434.

Local login takes **any** code for the addresses in `TRUSTED_EMAILS`; `123123` works. The
address is in `.claude/local-context.md` below — the value in `.env.local` is a placeholder,
and the real one is overridden in `.env.local.secrets`, which holds live API keys and is
denied by `settings.json`. Never read that file. Restored days reference photos in
production GCS, so those images render broken locally — expected.

Redis invalidates on writes through the API, so editing the database directly leaves
`/auth/me` and friends serving the pre-edit row — a test set up with `psql` can silently
verify nothing. Flush first:

```bash
docker exec memoryful-redis-local redis-cli -a dev_redis_password --no-auth-warning flushall
```

## Rules

- **Commit only when asked.** I read the whole diff first. When I do ask, write the message
  and commit yourself; don't hand it back for me to paste.
- **Work lands on `dev`, never `main`.** Check the branch before committing — a commit that
  lands on `main` is a headache to move. The workspace-root repo only has `main`.
- **Comment only what's genuinely surprising, in one line.** If a decision needs a paragraph
  to defend, refactor until it doesn't. Rationale belongs in the commit message.
- **American English everywhere** — `color`, `initialize`, `behavior`, `canceled`. Exception:
  names a library or spec owns, like `settings_customise_sources` and `aria-labelledby`;
  "correcting" those breaks the binding.
- **Mobile counts as much as desktop.** Check every visual change at phone width; anything
  that only misbehaves there is tagged `mobile` on the board.
- **Finished work goes in a TickTick *comment*, never over the task body.** The body is the
  brief, and a completion report written over it destroys what made the task worth keeping.
  Same when the body turns out to be *wrong*: correct it in a comment, so the correction
  reads as one. Keep it to a few lines — what changed, and what would bite the next person;
  the diff holds the detail. The 1024-char cap truncates silently, but it's a backstop, not
  a target: a comment trimmed to fit was already too long.
- **Never *change* anything in production.** No `docker-compose.vm.yml`, no
  `deploy-app.sh`, no deploying, nothing that writes. A hook blocks these; don't work around
  it. Local work runs against a *restored copy* of prod data.
  **Observing** prod is allowed, through one narrow door: the `production-analyzer` agent
  reads container status and logs over a fixed allow-list in `protect_prod.py`. Everything
  outside that list — including an interactive shell on the VM — stays denied. A refusal
  there is the design working; report it rather than rephrasing around it.
- **`.env.prod` is editable config, not a secret** — real secrets come from GCP Secret
  Manager in the VM at runtime. A new setting normally lands in `.env.local` *and*
  `.env.prod` in the same pass; only deploying it is off limits.
- **Always pass `--env-file .env.local`.** Compose otherwise auto-loads the bare `.env`,
  which is host tooling only, and silently leaves compose-level vars empty — classic symptom
  is Redis `invalid username-password pair`. Real secrets sit in gitignored
  `.env.local.secrets`, loaded after `.env.local` so it wins; `.env.local` is committed with
  placeholders, so never put a real key there.

## Commit convention

`type(scope): summary` — imperative, lowercase after the colon, no trailing period, under
~72 chars. Scope is the area touched, not the file.

Body only when the summary isn't enough: `- ` bullets, one per distinct change, saying
*what changed and why*, never restating the diff. No body is the common case.

```
fix(cache): clear day namespaces when a tag is mutated

ci(deploy): fail the deploy when the app never answers
- Poll the root route from inside the app container after recreating it, and
  exit non-zero with the log tail if it never responds
- A broken migration leaves uvicorn unstarted and the container gone, which
  previously still reported a successful deploy
```

A bullet claims what the commit *does*: "Eliminate the broken migration" is wrong for a
change that only *detects* one. Deployment tooling is `ci`, not `fix` — the pipeline
changed, the app didn't.

**One feature, one commit** — a working, revertable increment. Don't split a migration from
the model change that motivated it. Split only when a feature is genuinely large, along
boundaries that each stand alone. The other extreme is worse: if the body needs more than
~6 bullets, or the bullets are unrelated, that's two or three features wearing a trenchcoat.

Both repos commit in the same pass when a change spans them, with mirrored messages.

## Cross-repo

- The API contract is hand-maintained on both sides: `app/schemas/` in the backend,
  `src/api/*.ts` + `src/types/` in the frontend. No codegen — change one, change the other.
- A **new top-level API prefix** means editing the proxy regex in
  `memoryful-frontend/vite.config.ts`. Forgetting it is the usual cause of a new endpoint
  404-ing in dev while working fine in Swagger.
- `memoryful-backend/mcp_server/` exposes read-only tools over the same API. New read
  endpoints usually want a tool there too.

## Slash commands

`/stack-up` `/stack-reset` `/logs` `/db-refresh` `/migration` `/verify` — see `.claude/commands/`.

## Local context

Machine-local, gitignored, and safe to read — no secrets go in it.

@.claude/local-context.md
