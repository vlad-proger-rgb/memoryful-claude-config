---
name: comments-policy
description: Code comments in memoryful-backend and memoryful-frontend — none by default; when one is allowed, its length, and what to do instead. Use when writing, reviewing or cleaning up comments, docstrings or template comments.
---

# Comments Policy

Adapted from the MIT-licensed `comments-policy` skill in Dev-Toolbelt's `dev-team-agents`.

The guiding principle: **code should be self-documenting through clear naming**. Comments are the exception, not the rule.

---

## Core Principle — Default: No Comments

Code communicates intent through clear naming, small focused functions, and proper structure. Comments become outdated, double the maintenance burden, and often signal unclear code. If code needs a comment to explain why it is unusual, refactor it first.

**Before adding a comment, ask:**
- Can I make the code clearer with a better name or extracted method?
- Is this explaining WHAT (fix the code) or WHY (only valid reason)?
- Will this comment become outdated?

---

## When NOT to Comment

| Anti-pattern | Rule |
|---|---|
| Explaining what code does | Improve the code instead |
| Commenting bad code | Fix the code instead |
| Noise / obvious annotations | Remove them |
| Restating a type's shape (`// Array of tag IDs`, operators the type already lists) | Remove them — the type is the documentation |
| Labels on template blocks (`<!-- Tags -->`) | Remove them, or extract a component |
| Commented-out dead code | Delete it — Git history exists |
| Version-control comments | Use Git commits |
| TODO / FIXME / placeholders | Create a TickTick task with the `capture-task` skill |
| Dividers (`// === Section ===`) | Use proper structure — a composable in `src/composables/`, a component, or a module |
| Journal / attribution | Use Git blame |
| Closing brace markers (`} // end if`) | Refactor to smaller functions |
| Narrating the change or the old bug | Use the commit message or the TickTick comment |
| Dated or volatile facts (prices, retirement dates, "currently") | Remove them, or move them into config |
| Usage advice ("suited to X") | Remove it, or express it as a field the code reads |
| Describing what other files pass or do | Remove it |

A comment that is incorrect must be fixed or removed. A comment that mixes a restatement with a WHY is reduced to the WHY.

---

## When to Comment

| Case | Required? | Format |
|---|---|---|
| Business rule or product constraint | Yes — explains WHY | Inline comment stating the rule |
| Workaround for a browser, platform or library behavior | Yes — explains WHY | Inline comment naming the behavior |
| Value or class that looks wrong but is intentional | Yes — explains WHY | Inline comment stating the reason |
| Contract owned by the other repo or an external API | Yes — explains WHY | Inline comment stating the contract |
| Group label in a long flat declaration (settings fields, registration lists) | Allowed — organization | One short line naming the group (`# Postgres`) |
| Linter / type-checker suppression | Yes — directive | Narrowest code (`# type: ignore[code]`, `# noqa: X`, `eslint-disable-next-line rule`), with a reason when not obvious |

Examples from this codebase:

```html
<!-- 16px on mobile deliberately: iOS Safari zooms the page on focusing anything smaller -->
```

```python
# transaction pooling mode is incompatible with asyncpg's
# server-side prepared statement cache.
```

---

## Length Rule — Brief and Direct, Never a Block

When a comment is warranted (WHY, not WHAT), it must be **short**: 1 line as the default, 2–3 only when the constraint genuinely cannot be stated in one. State the rule/workaround/reference and stop — no restating of the surrounding code, no walkthrough of alternatives considered, no multi-paragraph rationale.

Hard limit: **max 3 lines per comment, max 3 comments per contiguous block** (e.g. per config section, per function). A comment that needs more than 3 lines to justify itself belongs in a commit message — not inlined. This applies everywhere, not only source code: config files (nginx, YAML, Dockerfiles, compose files, `.env.*`), infra scripts, and templates follow the same limit.

| Anti-pattern | Fix |
|---|---|
| Multi-line header block above a config section explaining history/context | One line stating the constraint; move the rest to the commit message |
| Walking through what was tried before landing on this line | Delete — Git history already has this |
| Repeating the same WHY across several lines or files | State it once, at the code that acts on it |

---

## Quick Reference

```
Need to add a comment?
├─ Explaining WHAT code does?            → ❌ Improve the code instead
├─ Explaining WHY (rule/workaround)?     → ✅ Add it, max 3 lines
├─ Type info?                            → ❌ Use type hints / TypeScript types
├─ Linter or type-checker suppression?   → ✅ Narrowest directive
└─ Something to do later?                → ❌ Create a TickTick task
```

---

## Docstrings and JSDoc

Not required, including for public functions. Write one only when a caller needs information the signature cannot give: a side effect, an ordering requirement, a non-obvious unit. Prefer one line over an `Args:` / `@param` block that restates typed parameters.

Type hints and TypeScript types document shapes — prefer them over prose comments:

```python
# BAD — prose for type info
# returns a dict mapping user_id to list of roles
def get_user_roles():
    ...

# GOOD
def get_user_roles() -> dict[str, list[str]]:
    ...
```

---

## Existing Code

When a change touches a file, apply this policy to the lines the change touches, not the whole file. A dedicated cleanup runs as its own task, one repo and one area at a time.
