---
name: daily-dashboard
description: Triages a user's GitHub inbox — unread notifications, assigned issues, review-requested and own PRs — into a prioritized daily dashboard. Use when the user wants a daily triage, standup summary, "what needs my attention today", or an urgency-ranked view of their GitHub notifications, issues, and pull requests. Do NOT use when the user wants to draft or write a single new issue (use writeup-github-issues).
allowed-tools: github-mcp-server Bash(gh:*)
---

# Daily Dashboard

You help a developer start their day by triaging their GitHub inbox into a short, prioritized dashboard of what actually needs their attention — surfacing items where someone is waiting on them and filtering out noise.

## Step 1 — Determine scope

1. Identify the user's GitHub login: `gh api user --jq .login` (or `gh auth status`). If `gh` isn't authenticated, ask the user for their handle.
2. Infer sensible defaults and only ask if genuinely ambiguous:
   - **Window:** items with activity in the last 24h, plus anything currently awaiting the user regardless of age.
   - **Sources:** unread notifications, open issues assigned to them, open PRs that request their review, and their own open PRs.
   - **Scope:** all orgs/repos. If the user names an org/repo, filter to it.

## Step 2 — Gather the data

Prefer the `github-mcp-server` tools for notifications/issues/PRs when available; otherwise use the `gh` CLI. Concrete `gh` commands:

- Unread notifications: `gh api notifications --jq '.[] | {repo: .repository.full_name, title: .subject.title, type: .subject.type, url: .subject.url, reason: .reason, updated: .updated_at}'`
- Issues assigned to them: `gh search issues --assignee @me --state open --json title,repository,labels,updatedAt,url,number`
- Review requested from them: `gh search prs --review-requested @me --state open --json title,repository,labels,updatedAt,url,number`
- Their own open PRs (to catch failing CI / new review comments): `gh search prs --author @me --state open --json title,repository,labels,updatedAt,url,number`

Run independent fetches in parallel (or via subagents) to keep it fast. For any PR that looks relevant, check CI with `gh pr checks <url>` and review state with `gh pr view <url> --json reviewDecision,comments`. To detect "activity since I last commented", compare the last event/comment timestamp to the user's most recent comment on that thread.

## Step 3 — Score urgency

Rate each item **HIGH / MEDIUM / LOW** from multiple signals, not labels alone. When torn between two levels, pick the lower one — unless there is a direct ask or a security signal, which always wins.

**HIGH** — someone is blocked on the user, or it's time-sensitive:
- A direct @mention or an unanswered question/request awaiting their reply
- A review explicitly requested from them on an open PR
- Security items: Dependabot/security alerts, advisories, or `security`/ `vulnerability` labels
- Incident/SLA labels or `urgent`/`critical`/`high`/`p0`/`p1`
- Failing CI on one of their own open PRs

**MEDIUM** — needs attention soon but no one is blocked right now:
- New activity since their last comment, without a direct ask
- Assigned issues with recent movement
- `medium`/`p2` labels; their own PRs with fresh (non-blocking) review comments

**LOW** — FYI / can wait:
- No recent activity or stale (no updates in ~30 days)
- Subscribed/`mention`-reason threads with no direct involvement
- Automated bot chatter (unless security-related)

Deduplicate: a notification and the issue/PR it points to are one item. Drop anything that clearly needs no action from the user.

## Step 4 — Output the dashboard

Output the Markdown dashboard and nothing else (no preamble or follow-up questions). For every HIGH item, include a concrete **next action**.

```markdown
# Daily Dashboard — <date>

## Summary
- Items needing attention: X (🔴 X · 🟡 X · 🟢 X)
- Waiting on you: X

## 🔴 High
- [Title](url) · `owner/repo` · Issue/PR/Alert · _why it's urgent_
  → **Next action:** <what to do next>

## 🟡 Medium
- [Title](url) · `owner/repo` · Issue/PR · _why_

## 🟢 Low
- [Title](url) · `owner/repo` · Issue/PR · _why_
```

If a section is empty, write "_Nothing here._" rather than omitting it. If there is genuinely nothing to act on, say so plainly.
