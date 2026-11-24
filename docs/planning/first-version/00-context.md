# 00 Context: budget-app / first-version

Answers in the user's words (picked options quoted as chosen).

## Project and plan id
- "Yes: budget-app / first-version" — new project `budget-app`, plan id `first-version`.

## Outcome
- Who uses it: "Several users, each signs in" — separate accounts, each user sees only their own data.
- "Current" for the pie chart: "User-chosen period" — pick a month or a date range on the dashboard.

## Deployment
- "Only on this machine" — local, nothing deployed.

## Outcome (continued)
- Out of scope: "Bank/card import, Multiple currencies" — all entries typed in by hand; one currency only.
- Not marked out of scope (left open): per-category budgets/limits and alerts; shared household budgets.
- Deadline: none given.

## Seams
- Sign-in: "Email + password, local" — accounts stored in the app's own database, passwords hashed; no external service.

## Constraints
- Recurrence: "Recurring + one-off" — income streams and expenses can be monthly/weekly etc. or single entries with a date.
- Stack: "Workspace defaults + SQLite" — Python API (e.g. FastAPI), React+TS front end, SQLite file database, a chart library chosen in planning.

## Outcome (continued, round 3)
- In scope: "Budgets/limits in scope, Shared budgets in scope" — users set a spending limit per category and see when it's exceeded; users can share a budget with other users.
- Categories: "Defaults + user's own" — a starter set (Housing, Food, Transport...) that each user can add to, rename or delete.

## Resources
- "None" — fully self-contained; no external APIs, no models, no spending.
- No LLM or agent behaviour, so no eval cases.

## Constraints (continued)
- Privacy: "Standard local handling" — SQLite file on this machine, users isolated from each other, no extra encryption.

## Sharing (round 4)
- "Shared budget = shared space" — a user creates a budget and invites others by email; every member sees and edits all of its income, expenses, categories and limits.
- "Yes, personal + shared" — every user has a private budget and can belong to shared ones; the dashboard switches between them.
- Invites: "In-app by email address" — the invite is matched to an account with that email and appears when they sign in. No email is sent.

Context declared complete by the user on 2026-11-24.

## Added after step 0 (2026-11-24)
- "remember this is a POC, I will be creating multiple fictitious accounts to test the data sharing. everythin is local"

## Answers to the step 1 open questions (2026-11-24, user's words)
- Q1 Donut composition: "yes, categories by color and total is total income of period. if it exceeds have the total become the total expenses and the total income becomes a red thick mark in the donut"
- Q2 Limit period: "user can choose las X days/weeks/months/years or open start/end calendar"
- Q3 Exceeded warning: "only exceed and show in both" (dashboard and entry form)
- Q4 Line charts: "see above and cumulative"
- Q5 Recurrence: "user chooses X days/weeks/months or a specific day of the month, for example paycheck is always 5th of the month"
- Q6 Income categories: "income by source and category"
- Q7 Deleting a category with expenses: "uncategorized"
- Q8 Shared budget roles: "anyone can invite, but invote is read only, no owners"
- Q9 Invites to an unknown email: "invite waits, user needs to accept invite on login"
- Q10 Currency: "only usd for now"
- Q11 Test data: "agent will run tests"
- Q12 Browsers: "start with chrome only"
- Q13 Repo and CI: "https://github.com/gacuchac/simple-budgeting.git gacuchacbot is collaborator"
- Q14 Session and password rules: "until signout, minimum 8 char length, at least 1 number and 1 special character"

## Follow-ups to the step 1 answers (2026-11-24)
- Q8 clarified: "Invited members view only" — whoever created the shared budget edits it; invited members can see but not edit. Everyone may invite.
- Q2 limit amount: "Limit set per period type" — the user sets each limit with its own period (e.g. $200/week, $500/month); it is compared pro-rated to the chosen range.
- Q13 remote: "Replace remote history" — add the remote and force-push local main, dev and uat over it, dropping the README-only commit.
- "Accept all defaults":
  - Line charts: one chart with two cumulative lines (income vs expenses), with daily, weekly or monthly buckets picked automatically from the range.
  - Editing a recurring entry changes it from a chosen date onward.
  - A recurrence on day 31 falls back to the month's last day.
  - Each budget has its own categories, seeded with the defaults.
  - Members can leave a shared budget; invites can be revoked.
  - Q11: tests create made-up accounts themselves on a throwaway database, plus a seed command for demo data.
  - CI gets a front-end job.

## Answers to the step 2 questions (2026-11-24, user's words)
- Red mark when a period has no income: "mark goes at income amount, so in this case it would be 0"
- Whether the creator can leave or delete a shared budget, and who can revoke invites: "yes"
- Whether income gets its own seeded categories: "yes"
- Whether view-only members see limits: "yes"
- Whether step 3 may open the CI spike PR: "yes" — a spike branch and draft PR on gacuchac/simple-budgeting, for step 3 only.
- Who can revoke a pending invite: "Creator + whoever sent it" — the creator can revoke any invite; a view-only member can revoke the invites they sent.
- When the creator of a shared budget leaves: "Leaving = delete" — the creator can only delete the shared budget, not leave it; members lose access.
