---
description: Capture an observation into the Memoryful TickTick board
argument-hint: <what you noticed, in plain words>
allowed-tools: mcp__ticktick__create_task, mcp__ticktick__search_task, mcp__ticktick__get_project_with_undone_tasks, Read, Grep, Glob
---

Capture this into TickTick:

$ARGUMENTS

Follow the `capture-task` skill for the board structure, tag list, priority scale and the
writing standard. In short:

1. **Investigate before writing.** Find the relevant code and put real file paths and
   function names in the task body. My description above is the symptom, not the research —
   a task worth keeping is one that's still actionable in six months.
2. `search_task` first to check I haven't already filed this.
3. Choose the column by where the work happens, tags from the existing list only, and
   priority from `0/1/3/5` — default `0` unless there's a real reason.
4. Show me the title, column, tags, priority and body **before** creating it. If anything
   is ambiguous — especially priority or whether it duplicates an existing task — ask
   rather than guessing.

Do not create a GitHub issue. That happens when work starts, not at capture.
