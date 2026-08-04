# Memoryful — Claude Code configuration

The agent configuration for the Memoryful workspace. This repo exists on its own because
the config lives in a **parent directory** of the two application repos, which are versioned
separately and can't carry it.

```bash
Memoryful/                   <- this repo
├── CLAUDE.md                   workspace context loaded every session
├── .mcp.json                   MCP servers (secrets are ${VAR} refs, never literals)
├── .claude/
│   ├── settings.json           permissions + hooks
│   ├── settings.local.json     personal, gitignored — tokens live here
│   ├── launch.json             dev server definitions
│   ├── commands/               slash commands
│   ├── skills/                 model-triggered instructions
│   ├── agents/                 subagents
│   └── hooks/                  deterministic guardrails
├── memoryful-backend/        <- separate repo, ignored here
└── memoryful-frontend/       <- separate repo, ignored here
```

Each application repo carries its own `CLAUDE.md` and `.claude/settings.json`, versioned
with that repo. Only the workspace-level configuration lives here.

## Setting up a new machine

```bash
git clone <this-repo> Memoryful
cd Memoryful
git clone <backend-repo>  memoryful-backend
git clone <frontend-repo> memoryful-frontend
cp .claude/settings.local.json.example .claude/settings.local.json   # then fill in tokens
```

`settings.local.json` is deliberately absent from the repo. It carries the TickTick API
token and any machine-specific overrides; recreate it from the example and paste tokens
from your password manager.

## What's in here

**Commands** — `/stack-up` `/stack-reset` `/logs` `/db-refresh` `/migration` `/verify`
`/api` `/task`

**Skills** — `backend-endpoint` (the six places an API change touches), `capture-task`
(filing work into the TickTick board)

**Agents** — `migration-reviewer` (audits generated Alembic revisions)

**Hooks** — `protect_prod.py` refuses commands that would run against production;
`format_file.py` runs black/isort or prettier on save; `ticktick_scope.py` lets task
creation through only when it's addressed to the triage column.

## Conventions

Written in American English. Commit messages follow `type(scope): summary` — see the
commit convention section in `CLAUDE.md`.
