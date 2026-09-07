# Project Coordination Agent Constraints

This directory is a local coordination project for two independent Git repositories. It is not a monorepo.

## Repository layout

- `.` is the meta repository. It tracks this policy, `.gitignore`, and the three `planning-with-files` task files: `task_plan.md`, `findings.md`, and `progress.md`.
- `AutoWSGR/` is the independent backend repository.
- `AutoWSGR-GUI/` is the independent GUI repository.
- The child repositories and all worktrees are ignored by the meta repository. Never add them as submodules or stage their contents from here.

## Task identity

- Every task gets a unique local ID: `YYYYMMDD-<slug>-<short-id>`.
- A cross-repository task uses the same ID and branch name in all involved repositories.
- Use branches named `codex/<task-id>` and keep them local unless the user explicitly requests a remote operation.
- The first lines of the meta `task_plan.md` must identify `Task ID`, `Task Status`, and `Next Step`.
- `Task Status` is one of `in_progress`, `blocked`, or `done`.

## Start and resume

1. Identify this meta repository and each child repository with `git rev-parse --show-toplevel`.
2. Run `git status --short --branch` and do not alter existing user changes.
3. Run `git worktree list --porcelain` and enumerate local `codex/*` branches in the meta repository.
4. Read each candidate meta worktree's `task_plan.md`. Resume a matching `in_progress` task; do not create a duplicate. A `blocked` task needs explicit user direction.
5. If no task matches, create a new meta worktree and branch, then create matching child worktrees only for repositories the task touches.

## Isolation

- Never run `git switch` or `git checkout` in the shared project or child-repository worktrees to begin work.
- Each task uses this layout under `.worktrees/<task-id>/`: `meta/`, `AutoWSGR/`, and `AutoWSGR-GUI/` as applicable.
- The meta worktree contains the three planning files. Child worktrees contain only their repository's code and repository-specific task changes.
- A branch already attached to a worktree is a resume candidate, not a new branch target. Git's one-branch-per-repository-worktree rule is an isolation guard.

## Planning and lifecycle

- `planning-with-files` standard filenames are task-scoped. Never use one shared copy in the parent directory for concurrent tasks.
- Update `task_plan.md` at phase boundaries, record discoveries in `findings.md`, and record actions/errors in `progress.md`.
- Commit planning checkpoints in the meta task branch and code checkpoints in the relevant child branches.
- Before completion, set `Task Status: done` and record the child commit SHAs in `progress.md`.
- Do not delete a task automatically. After code is merged or cherry-picked, cleanup may remove the task worktrees and branches only after confirming they are clean and no longer needed.

## Rule layering

The global `AGENTS.md` defines the generic concurrency protocol. This file defines this three-repository topology. `AutoWSGR/AGENTS.md` and `AutoWSGR-GUI/AGENTS.md` define their own code, test, build, and release constraints. A more-specific rule may narrow the workflow but may not weaken user-change preservation, security, validation, or isolation requirements.
