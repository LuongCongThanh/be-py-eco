# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- Create: `gh issue create --title "..." --body "..."`
- Read: `gh issue view <number> --comments`
- List: `gh issue list --state open`
- Comment: `gh issue comment <number> --body "..."`
- Labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`
- Close: `gh issue close <number> --comment "..."`

Infer the repository from `git remote -v`.

## Pull requests as a triage surface

PRs are not used for triage or request intake — only GitHub issues are. A PR
exists solely to ship code/docs for work already tracked by an issue (see
`docs/agents/git-workflow.md`); it should link back with `Closes #<number>`,
not introduce new scope of its own.

## Skill conventions

- "Publish to the issue tracker": create a GitHub issue.
- "Fetch the relevant ticket": run `gh issue view <number> --comments`.
- `/wayfinder` uses a `wayfinder:map` issue with linked child issues.
- Claim work using `gh issue edit <number> --add-assignee @me`.
- Represent blocking relationships with GitHub issue dependencies, falling back to a `Blocked by:` line when necessary.
