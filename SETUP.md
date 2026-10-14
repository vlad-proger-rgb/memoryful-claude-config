# Setting up Memoryful on a new machine

Everything a fresh machine needs beyond `git clone`, on Windows or macOS. Most of the work
is the gitignored files: the repos clone fine without them, then fail in ways that don't
point back at the missing file.

## 1. Install

| Tool | Why |
| --- | --- |
| Git | three repos |
| Docker Desktop | the whole backend stack |
| Python 3.13 | host venv for editor tooling and the Claude Code hooks |
| Node.js + npm | frontend dev server |
| Claude Code | the agent setup in this repo |
| VS Code or other IDE | `.vscode/` carries the tasks and workspace settings |

The hooks run `python`, falling back to `python3`, and refuse to run without either, so a
stock macOS is enough for them. On macOS, put the Homebrew Python on `PATH` in
`~/.zprofile`, not `~/.zshrc`: `.zshrc` runs in every new shell and pushes it back in front
of an already-activated venv.

The `postgres-local` MCP server in `.mcp.json` runs through `uvx`, so it needs
[uv](https://docs.astral.sh/uv/) installed; without it that server never connects.

## 2. Clone

```bash
git clone git@github.com:vlad-proger-rgb/memoryful-claude-config.git
cd memoryful-claude-config
git clone git@github.com:vlad-proger-rgb/memoryful-backend.git
git clone git@github.com:vlad-proger-rgb/memoryful-frontend.git
git -C memoryful-backend switch dev
git -C memoryful-frontend switch dev
```

## 3. Bring over the gitignored files

Synced between machines by hand. None of them is in any repo.

### Workspace root

| Path | What it holds | Without it |
| --- | --- | --- |
| `.claude/settings.local.json` | TickTick token, enabled MCP servers, MCP permissions. Start from `settings.local.json.example`. | TickTick MCP fails to connect |
| `.claude/local-context.md` | Local login address, prod VM SSH user. No secrets. | Claude doesn't know which address logs in locally |

### `memoryful-backend/`

| Path | What it holds | Without it |
| --- | --- | --- |
| `.env.local.secrets` | Real values over `.env.local`'s placeholders: `LLM_MODE`, OpenAI/Anthropic keys, `TRUSTED_EMAILS`. Template: `.env.local.secrets.example`. | Stack boots on placeholders: AI calls fail, and your address isn't trusted, so the `123123` login doesn't work |
| `secrets/google/service-account.json` | GCP service account (`GCP_CREDENTIALS_PATH`) | Every Celery worker dies on boot with `DefaultCredentialsError` |
| `backups/neondb_backup_latest.dump` | Copy of prod data, restored automatically into a fresh database | Database starts empty and `init_db.py` seeds demo data; your account isn't there |
| `bucket_base/` (~6 MiB) | Seed content synced into SeaweedFS on first boot | Seeded storage files missing |
| `.env` | Host tooling only: the production connection string for `/db-refresh`. Compose must never load it. | Can't dump a fresh copy of prod; restoring an existing dump still works |
| `mcp_server/.env` | Optional, only for running the MCP server on the host. Template: `.env.example`. | Nothing, when the server runs in Docker |

### `memoryful-frontend/`

| Path | What it holds | Without it |
| --- | --- | --- |
| `.env` | `VITE_GOOGLE_CLIENT_ID`, which must be one of the backend's `GOOGLE_CLIENT_IDS` | The Google sign-in button is replaced by an "unavailable" note |

Leave `VITE_API_BASE_URL` unset. Dev then goes through the Vite proxy to `localhost:8000`;
copying the production value from `.env.example` points the dev app at the live API.

## 4. Start and check

```bash
# from memoryful-backend/
docker compose -p memoryful --env-file .env.local -f docker/docker-compose.local.yml up --build -d
```

Ollama runs on CPU by default. Add `-f docker/docker-compose.gpu.yml` only on a machine
with an NVIDIA GPU. On Apple Silicon the Pub/Sub emulator runs as amd64 under emulation,
which is fine.

Before calling the machine done, confirm:

- `docker logs memoryful-db-local | grep init-restore` shows `Restoring … Done.`
- `docker logs memoryful-celery-local` shows five workers `ready.`
- `npm run dev`, then `http://localhost:3000` → your address + `123123` lands on
  `/dashboard` with your real days, not on the new-user details step.
- The Google button renders on the login page.
- `/verify` is all green.

## 5. Per-machine editor setup

These live in the editor's own storage or user settings, so no repo can carry them.

- **Automatic tasks.** The BE/FE/GCS/Py terminals start on folder open only when user
  settings have `"task.allowAutomaticTasks": "on"`. The editor asks once per workspace;
  dismissing that prompt counts as "no" and it never asks again.
- **Python interpreter.** Select `memoryful-backend/.venv/bin/python`
  (`.venv\Scripts\python.exe` on Windows). mypy runs from that interpreter. On macOS, type
  the path instead of browsing: the file picker follows the venv's symlink to the Homebrew
  binary, which the editor rejects.
