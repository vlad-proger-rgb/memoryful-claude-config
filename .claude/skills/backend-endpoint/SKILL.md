---
name: backend-endpoint
description: Use when adding, changing or removing a Memoryful API endpoint — creating a FastAPI route, adding a Pydantic schema, wiring a new router, changing what a response returns, or exposing a resource to the Vue frontend. Covers the Msg envelope, the Redis cache namespaces that must be invalidated, router registration, the vite proxy, and the MCP tool mirror.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adding or changing a backend endpoint

Up to six places may need to change, depending on the endpoint. Missing one is the usual
cause of "it works in Swagger but not in the app" or "the UI shows stale data".

## 1. Model — `app/models/`

Only if the shape of stored data changes. A model edit means a migration: use `/migration`.

## 2. Schema — `app/schemas/`

Pydantic. Read from ORM objects with `T.model_validate(obj)`. Export it from the package
`__init__` so routers can do `from app.schemas import ...`.

## 3. Router — `app/routers/<resource>.py`

Routers are **thin and query the DB directly** — there is no service or repository layer.
Follow the existing shape exactly:

```python
router = APIRouter(prefix="/tags", tags=["Tags"])

@router.get("/", response_model=Msg[list[T]])
@cached(expire=CACHE_TTL_USER_DATA, namespace="tags")
async def get_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[UUID, Depends(get_current_user())],
) -> Msg[list[T]]:
    stmt = select(Tag).where(Tag.user_id == user_id)
    ...
    return Msg(code=200, msg="Tags retrieved", data=[...])
```

Non-negotiables:

- **Every response is `Msg[T]`** — `code`, `msg`, `data`. Never return a bare model or dict.
- **`get_current_user()` is called**, not passed bare: `Depends(get_current_user())`.
- **Every query filters on `user_id`.** This is the entire tenancy boundary; a `select`
  without it leaks another user's data. Check this on reads *and* writes — an `update`
  or `delete` scoped only by `id` is a vulnerability, not a bug.
- Full type annotations on every def. mypy runs with `disallow_untyped_defs` and
  `warn_return_any`; an unannotated handler fails the build.
- Built-in generics only — `list[T]`, `dict[K, V]`, `X | None`. Never `typing.List`,
  `typing.Dict` or `Optional[X]`. `Annotated` and `Literal` still come from `typing`.
- `raise HTTPException(404, "...")` for not-found. Shared handlers live in
  `app/core/exceptions.py`.

## 4. Cache invalidation — the subtle one

Reads are wrapped in `@cached(namespace=...)`; writes must call `await clear_cache(ns)` for
**every namespace whose payload embeds this data**, not just its own. Tags are embedded by
value inside `DayDetail`/`DayBase`, so `app/routers/tags.py` clears three namespaces on
mutation:

```python
await clear_cache("tags")
await clear_cache("days_list")
await clear_cache("days_detail")
```

Before finishing a write endpoint, grep the schemas for the model you just mutated and clear
every namespace that serializes it. Symptom of getting this wrong: the change is in the DB
but the UI keeps showing the old value until the TTL expires.

## 5. Register the router — `app/main.py`

Two edits: add to the `from app.routers import (...)` block *and* add
`app.include_router(x.router)`. A new router file that isn't registered simply 404s.

## 6. Frontend + MCP

- `memoryful-frontend/src/api/<resource>.ts` and `src/types/` — hand-maintained, no codegen.
- **New top-level path prefix?** Add it to the proxy regex in
  `memoryful-frontend/vite.config.ts`, or it 404s in dev while working fine in Swagger.
- Read-only endpoints usually deserve a matching tool in `mcp_server/tools/` with a test in
  `mcp_server/tests/`.

## Verify

`docker exec memoryful-app-local mypy`, then hit the route on `http://localhost:8000/docs`.
