---
description: Call a local API endpoint with a real auth token (Postman-style, from the terminal)
argument-hint: <METHOD> <path> [json-body]
allowed-tools: Bash(curl:*), Bash(python:*), Bash(docker:*), Read, Grep
---

Hit the local API at `http://localhost:8000`.

**Getting a token.** `POST /auth/verify-code` takes `{"email": ..., "code": ...}`. Addresses
listed in `TRUSTED_EMAILS` skip verification entirely, so any code works. No email is sent by
this route — `verify-code` has no send path at all, and `request-code` guards its
`send_email_task.delay(...)` behind the same trusted check. Go straight to `verify-code`;
calling `request-code` first is unnecessary.

The address isn't hardcoded here — read the first entry of `TRUSTED_EMAILS` at runtime.
Check `.env.local.secrets` **first**, since compose loads it second and a value there
replaces the committed one outright:

**Take the first non-placeholder entry, not the first entry.** `.env.local` currently lists
`dev@example.com,your-email@example.com,<real>` — so `cut -d, -f1` picks a placeholder:

```bash
EMAIL=$(grep -h '^TRUSTED_EMAILS=' memoryful-backend/.env.local.secrets memoryful-backend/.env.local 2>/dev/null \
  | head -1 | cut -d= -f2 | tr ',' '\n' | grep -v 'example\.com' | head -1)
```

This matters more than it looks. Any address in the list authenticates, but one with no row
in the restored dump **silently auto-creates an empty user** — so every endpoint returns
`0 rows` and the restore looks like it failed when it worked fine. If the result is empty or
still looks like a placeholder, stop and say so rather than authenticating with it.

The token is at `data.tokens.accessToken` in the `Msg` envelope. Extract it robustly — the
schemas are camel-cased via `CamelModel`, so accept either casing:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/verify-code \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"code\":\"123123\"}" \
  | python -c "import sys,json; t=json.load(sys.stdin)['data']['tokens']; print(t.get('accessToken') or t['access_token'])")
```

**Then make the call.** The request is: `$ARGUMENTS`

Parse that yourself — first token is the method, second the path, anything after is a JSON
body. **Don't rely on `$1`/`$2`/`$3` here**; positional substitution has misfired on this
command (`$1` picked up the path instead of the method), and shell forms like `${3:+-d $3}`
are never interpolated at all. `$ARGUMENTS` is the whole string and is reliable.

```bash
curl -sL -X GET "http://localhost:8000/tags/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w '\n%{http_code}' -o /tmp/resp.txt
```

Keep the status code out of the body — appending `-w` to stdout and piping into
`python -m json.tool` makes the parse fail, since the trailing status line isn't JSON. Write
the body separately, pretty-print it, then report the code.

**Trailing slashes matter.** Collection routes are `@router.get("/")` under a prefix, so
they live at `/tags/`, `/days/`, `/insights/` — requesting `/tags` returns **307**, not
data. Item routes (`/auth/me`, `/tags/{id}`) have no trailing slash. Pass `-L` so a redirect
resolves rather than being reported as an empty result; 307 preserves the method and body,
so it's safe for writes too.

Report the status code and the pretty-printed body. If it's a 4xx/5xx, pull the app
container's recent logs and explain the actual cause rather than restating the error.

Reuse `$TOKEN` across calls within one task instead of re-authenticating each time. Never
paste a token into a file — it stays in the shell.
