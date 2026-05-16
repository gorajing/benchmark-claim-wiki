# Agent Coordination Tracker

Use this document to keep the work split clear while multiple agents are active.

## Current Roles

| Role | Branch | PR | Scope | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Agent 1 | TBD | TBD | TBD | TBD | TBD |
| Agent 2 | TBD | TBD | TBD | TBD | TBD |
| Agent 3 | TBD | TBD | TBD | TBD | TBD |
| Integration Manager | main or integration branch | TBD | Review overlap, test combined changes, choose merge order | Active | Codex |

## Required Agent Update

Each agent should post this update at the start and end of work:

```text
Agent:
Task:
Branch:
PR:
Files I expect to edit:
Files I changed:
Tests/checks run:
Risks or TODOs:
Potential overlap with other agents:
```

## Integration Checklist

- [ ] Confirm every agent is on a separate branch or worktree.
- [ ] Collect branch names and PR links.
- [ ] Compare changed files across branches.
- [ ] Identify shared-file ownership.
- [ ] Run unit tests.
- [ ] Run the demo or smoke check.
- [ ] Inspect GitHub CI for each PR.
- [ ] Decide merge order.
- [ ] Re-test after each merge or combined integration branch.

## Merge Order Notes

Record planned merge order here once branches are known.

1. TBD
2. TBD
3. TBD

## Shared File Watchlist

Add any file here that more than one agent expects to touch.

- TBD
