# Git Workflow

Three-tier branching: `main` (production) ← `dev` (integration) ← feature branches.
`master` is legacy and frozen — do not branch from or merge into it.

> **No CI yet.** `main`/`dev` require a PR to merge, but there is no GitHub Actions
> workflow enforcing lint/tests — the repo has no Python code yet. Once real code
> lands, add `.github/workflows/ci.yml` (lint + pytest) and wire it as a required
> status check on `main` and `dev` branch protection so the PR checklist item
> "tests passing" is actually verified, not just self-reported.

## Branch roles

- **`main`** — production/release branch. Default branch on GitHub. Protected: PR required,
  no direct pushes, no force-push, no deletion.
- **`dev`** — integration branch. All feature/fix/chore work merges here first. Protected
  the same way as `main`: PR required, no direct pushes.
- **`feature/*`, `fix/*`, `chore/*`** — short-lived branches, always created from `dev`.
- **`master`** — kept for history only. Frozen: no new commits, no merges in or out.

```text
main   ──────────────────────●──────────────●───────  (release merges from dev)
                               \              \
dev    ──●──●──●──●──●──●──●───●──●──●──●──●───●────  (integration; feature PRs land here)
          \        \                 \
feature/*  ●──●──●   fix/*  ●──●       chore/*  ●──●
```

## Branching

Always branch from `dev`, never from `main` or `master`:

```bash
git checkout dev
git pull
git checkout -b feature/123-add-login
```

- `feature/<short-description>` — new functionality
- `fix/<short-description>` — bug fixes
- `chore/<short-description>` — tooling, docs, refactors with no behavior change
- Prefer including the issue number when one exists, e.g. `feature/123-add-login`

## Committing

- Small, focused commits with clear messages (imperative mood: "Add", "Fix", "Refactor").
- Format: `<type>: <summary>` where type is one of `feat|fix|chore|docs|refactor|test|perf`.
- Reference the issue when relevant: `Refs: #123` in the commit body, or `Fix session timeout (#123)` in the summary.
- A local commit template is configured (`.gitmessage`, wired via `git config commit.template`) —
  running plain `git commit` (no `-m`) opens it with the expected structure.

## No AI attribution

Do not mention any AI agent or tool name (Claude, Codex, Copilot, GPT, ChatGPT, Cursor, etc.)
anywhere in this repo's git history or GitHub activity — not in commit messages, commit
trailers (no `Co-Authored-By: <AI name>`), PR titles/bodies, or PR/issue comments. Write
commits and PRs as if authored by the human driving the session. This applies to every
agent working in this repo, regardless of that agent's own default commit conventions.

## Opening a Pull Request

Feature/fix/chore branches always target `dev`:

```bash
git push -u origin feature/123-add-login
gh pr create --base dev --fill
```

- Link the PR to its issue (`Closes #123` in the PR body) so it auto-closes on merge.
- Keep PRs small and scoped to one concern.
- `.github/PULL_REQUEST_TEMPLATE.md` is auto-applied by GitHub for PRs opened via the web UI,
  and by `gh pr create` when no `--body`/`--fill` is passed (`--fill` uses commit messages instead).

## Merging into dev

- Squash-merge once approved and CI passes:

```bash
gh pr merge --squash --delete-branch
```

## Releasing dev → main

When `dev` is ready to ship, open a PR from `dev` into `main`:

```bash
gh pr create --base main --head dev --title "Release: <summary>"
gh pr merge --merge   # prefer a real merge commit here, not squash, to preserve dev history
```

## Hotfixes

For an urgent fix to production that can't wait for the normal `dev` cycle: branch
`fix/<description>` from `main`, PR it back into `main`, then immediately open a
follow-up PR merging `main` back into `dev` so the fix isn't lost on the next release.

## Skill conventions

- "Start work on an issue": create a `feature/<issue>-<slug>` or `fix/<issue>-<slug>`
  branch from `dev`.
- "Ship the change": open a PR against `dev` with `gh pr create --base dev --fill`, link
  the issue, and squash-merge once green.
- "Cut a release": open a PR from `dev` into `main` and merge (no squash).
- See `docs/agents/issue-tracker.md` for issue conventions and `docs/agents/triage-labels.md`
  for label vocabulary.
