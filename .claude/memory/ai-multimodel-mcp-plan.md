---
name: ai-multimodel-mcp-plan
description: Memoryful AI stack — multi-model routing, MCP tool-calling, SSE streaming — decisions, gotchas, and what is left
metadata:
  type: project
---

Multi-model routing, MCP tool-calling, SSE streaming and persisted tool calls are shipped.
Verify any status claim here with `git branch --contains` before relying on it.

**Left:** exposing the MCP server publicly (`mcp.memory-ful.com`: nginx block to :3001, TLS,
DNS — `docker/nginx.conf` has none yet), capturing token usage (`usage_metadata` is
discarded), and Phase 5 below.

## Decisions

- Claude uses the **direct Anthropic API, not Vertex** — Google denied the per-model quota.
- The in-app agent calls the **running MCP server over streamable-HTTP**
  (`langchain-mcp-adapters`), forwarding the request's bearer — one tool surface for in-app
  and external clients.
- Chat services are classes: `ChatStore` (persistence) and `ChatAgent` (turn engine).
- Tool blocks and timestamps live in the `chats.messages` JSON column. Dump with
  `model_dump(mode="json")` or datetimes break it.

## Gotchas

- FastMCP's `get_http_headers()` strips `authorization` — needs `include={"authorization"}`.
- `MCP_SERVER_URL` must have no trailing slash — `/mcp/` 307s to `/mcp`.
- Gemini returns content blocks, not a string — use `_extract_text()`.
- Newer Claude/OpenAI models 400 on `temperature` — see `_ANTHROPIC_NO_SAMPLING`. Read the
  `claude-api` skill before touching Claude code.
- Vertex OpenAI-compat (Grok/MaaS) 400s on empty assistant tool-call content.
  `_VertexMaaSChatOpenAI` pads it and must override `_stream`/`_astream` as well as
  `_generate`/`_agenerate`.
- SSE behind nginx needs `proxy_http_version 1.1`, `Connection ""`, `proxy_buffering off`.
- Backend `.py` files are CRLF — multi-line replacements written with `\n` silently no-op.
- Grok via Vertex exposes no reasoning channel.

## Phase 5 — @-referenced day attachments — parked

`feat/day-attachments` in both repos (`e637a6f` backend, `1d029a9` frontend), never
runtime-tested. Parked because the 1GB prod VM is already swapping: the frontend preloads 60
full days on the first `@`, `_history()` re-injects every attached day's full text on every
turn, and nothing caps attachments per message.

The shipped chat attachment chip (`1e50a4e`, used by the weekly digest's "Discuss") is the
cheaper base for a redesign: one `ChatAttachment` per message, its `content` prefixed to the
sent text, no backend change. A day attachment built on it fetches only the picked day,
needs no per-turn re-injection, and is capped at one by design. The `+` button in
`AiChatInterface.vue` is still a "coming soon" toast — the natural entry point.

The maintainer is optimization-focused: per-request cost and caching are a standing concern.
