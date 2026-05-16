# Agent Coordination Rules

These rules apply to every automated agent working in this repository.

## Operating Model

- Codex is the integration manager for this repo.
- Each agent must work on its own branch or git worktree.
- Do not make feature changes directly on `main`.
- Keep changes scoped to the assigned task.
- Do not overwrite, revert, reformat, or clean up another agent's work unless the integration manager explicitly asks for it.
- If a task requires touching files that another agent may edit, pause and report the overlap before making the change.

## Start Of Work

Before editing files, each agent must report:

- assigned task
- current branch
- output of `git status --short --branch`
- expected files or directories to edit
- tests or checks expected to run

If the agent is not on an assigned branch, create or switch to one before editing.

Recommended branch name format:

```text
agent/<short-task-name>
```

## During Work

- Commit coherent checkpoints.
- Push the branch regularly when GitHub access is available.
- Keep PR descriptions updated with the current scope and risks.
- Avoid broad refactors unless they are part of the assigned task.
- Avoid formatting unrelated files.
- Leave unrelated dirty files untouched.

## Handoff

When finished, each agent must report:

- branch name
- PR number or link, if available
- files changed
- behavior changed
- tests or checks run, with pass/fail status
- known risks, TODOs, or assumptions
- any files likely to conflict with other agents

## Integration Manager Responsibilities

The integration manager will:

- inspect local branches and GitHub PRs
- compare changed files across agents
- identify conflicts and behavioral overlap
- run relevant tests and builds
- inspect failing CI when needed
- choose the safest merge order
- make integration fixes only when the scope is clear

## Conflict Protocol

If two agents need the same file:

1. Stop before editing the shared file.
2. Report the file path and intended change.
3. Wait for the integration manager to assign ownership or merge order.

No agent should resolve another agent's conflict by discarding their changes.
