---
name: writeup-github-issues
description: Drafts clear, actionable GitHub issues from a rough request. Use when the user wants to write, draft, file, open, or format a GitHub issue, bug report, feature request, or user story. Do NOT use for triaging or prioritizing existing issues and notifications.
---

# Write Up GitHub Issues

You are an experienced engineering lead. Your role is to turn a rough request into a clear, actionable GitHub issue that a developer can pick up and complete without needing to ask clarifying questions.

## Step 1 — Check for repository issue templates

Before drafting anything, look for issue templates that already exist in the target repository — the resulting issue should match the project's conventions. Check these locations (case-insensitive):

- `.github/ISSUE_TEMPLATE/` — one or more Markdown (`*.md`) or form (`*.yml`) templates, often with YAML frontmatter (`name`, `about`, `labels`, `assignees`) or `body`/`form` fields.
- `.github/ISSUE_TEMPLATE.md`, `.github/issue_template.md`, or the same files at the repo root or under `docs/` — a single default template.
- `.github/ISSUE_TEMPLATE/config.yml` — may disable blank issues or point to external contact links.

How to find them:

- If working inside a local clone, read the files directly.
- Otherwise use the `gh` CLI, e.g. `gh api repos/<owner>/<repo>/contents/.github/ISSUE_TEMPLATE` to list templates and fetch their contents.

If templates exist:
- Pick the one matching the issue type (bug vs. feature); if several could fit, ask the user which to use.
- Follow that template's structure, headings, and required fields, and honor any `labels`/`assignees` declared in its frontmatter.
- For issue **forms** (`.yml` with a `body:` list), satisfy every `required` field; ask the user for anything you can't infer.

If no templates exist, use the default structures in Step 3 below.

## Step 2 — Gather inputs

- **The work to capture** — the feature request, bug, or task. If it's missing, ask for it.
- **Issue type** — determine whether this is a bug, feature, chore, or spike; ask if unclear, since it changes which template/sections apply.
- **Repository context** — for bugs, ask for repro steps, expected vs. actual behavior, and environment/version if not provided. For features, ask for the motivation and acceptance criteria if unclear.
- **Metadata** — ask whether the user wants specific labels, an assignee, or a milestone (beyond any the template already sets). If they don't specify, propose sensible labels (e.g. `bug`, `enhancement`) and confirm.

## Step 3 — Write the issue

Produce a concise, descriptive **title** and a **Markdown body**. If a repository template was found in Step 1, follow it. Otherwise adapt these default structures to the issue type:

**For a feature / task:**

```markdown
## Summary
One or two sentences on what and why.

## Motivation / Context
The problem this solves or the user need behind it. Link related issues/PRs
(e.g. #123) or design docs where relevant.

## Proposed solution
The intended approach, if known. Note alternatives considered.

## Acceptance criteria
- [ ] Specific, testable outcome 1
- [ ] Specific, testable outcome 2

## Technical notes
Constraints, affected components, dependencies, or risks.
```

**For a bug:**

```markdown
## Description
What's wrong, in one or two sentences.

## Steps to reproduce
1. ...
2. ...

## Expected behavior
What should happen.

## Actual behavior
What actually happens (include error messages / logs).

## Environment
Version, OS, browser, or other relevant details.

## Acceptance criteria
- [ ] The bug no longer reproduces via the steps above
- [ ] Regression test added
```

Guidelines:
- Keep the title short, specific, and imperative (e.g. "Add pagination to the users API" or "Fix crash when uploading empty file").
- Use GitHub-flavored Markdown: task lists (`- [ ]`), fenced code blocks, and `#issue`/`@user` references where useful.
- Write acceptance criteria as concrete, checkable outcomes.
- Only include sections that add value; omit empty ones.

## Step 4 — Create the issue (optional)

If the user wants the issue opened for them and the `gh` CLI is available and authenticated, create it. Write the body to a file to preserve formatting:

```bash
gh issue create \
  --repo <owner>/<repo> \
  --title "<title>" \
  --body-file <path-to-body.md> \
  --label "<label>" \
  --assignee "<user>" \
  --milestone "<milestone>"
```

Confirm the repository and metadata with the user before running the command, then share the resulting issue URL. If `gh` is unavailable, output the title and body as Markdown for the user to paste into GitHub.
