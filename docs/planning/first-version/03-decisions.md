# 03 Decisions: budget-app / first-version (light planner I3)

The user's decisions in I3, in order, in their words.

## 1. Software architecture
- Question: approve the proposed software architecture (layers domain → db → repos → services → api → web, money as integer cents, a budget-access guard, front-end types generated from the API)? Full text: `~/Developing/.claude/runs/budget-app/first-version/architecture.md`.
- Answer: "Approve as written"

## 2. Over-limit warning on the expense entry form
- Question: which period should the "over limit" warning on the expense form compare against?
- Answer: "Limit's own period" — a $200/week Food limit is checked against the week containing the expense's date, including this new expense.

## 3. Build order
- Question: in what order should the features be built, so something works early?
- Answer: "Personal first, then sharing" — 1) sign-up, sign-in, a personal budget and entries; 2) the dashboard with charts and period picker; 3) limits; 4) shared budgets and invites, tested with alice and bob.

## 4. What proves sharing works
- Question: what proves the sharing works before the app counts as done?
- Answer: "API tests + one browser run" — API tests cover every role and isolation case; one Playwright run in Chrome signs in alice and bob on alice.localhost and bob.localhost, alice invites bob, bob accepts and sees but can't edit.

## 5. OI-1: how the expense form gets its LimitStatus (asked 2026-11-24, after I3)
- Question: the expense form must warn "over limit" for the limit's own period, counting the new expense. Add a new check route, or reuse the dashboard route and do the period arithmetic in the web?
- Answer: "New check route (Recommended)": `GET /api/budgets/{budget_id}/limits/check?category_id&date&amount_cents&exclude_entry_id`, returning one `LimitStatus` with the amount counted. Taken through the architecture skill.

## 6. OI-2: the split route's path
- Question: is contract 4's `POST /entries/{id}/split` meant as `POST /api/budgets/{budget_id}/entries/{entry_id}/split`, covered by the guard?
- Answer: "Yes, budget-scoped (Recommended)"

## 7. OI-3: a split at or before the rule's start
- Question: when the split date is on or before the rule's start, reject with 422 or update the whole series in place?
- Answer: "Edit in place (Recommended)"

## 8. Undecided defaults in PRD section 12
- Question: change any of the eight defaults (warning doesn't block; "last N" ends today; weeks start Monday; one limit per category; re-invite after decline; creator can't remove members; no note on entries; browser test local only)?
- Answer: "it's ok" (both groups). All eight defaults stand.
