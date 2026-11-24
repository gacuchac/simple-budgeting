# Progress: budget-app / first-version

- step 0, 00-context.md, 2026-11-24 11:42, context complete: multi-user local app (email+password), recurring and one-off entries, categories, limits, shared budgets, SQLite + FastAPI + React, no deploy, no external services.
- step 1, 01-research-and-stories.md, 2026-11-24 11:45, research, 15 user stories, 9 local seams in a risk register, 4 domain risks, 14 open questions.
- step 1 follow-up, 00-context.md, 2026-11-24 12:02, user answered the 14 open questions plus 4 follow-ups; remote gacuchac/simple-budgeting added and main/dev/uat force-pushed on user's OK.
- step 2, 02-alternatives.md, 2026-11-24 12:08, four whole-solution alternatives (A-D), seven shared mechanisms, 10 seams with 2-4 crossings each, falsifiable claims, five new questions.
- step 2 follow-up, 00-context.md, 2026-11-24 12:11, user answered step 2's five questions plus two follow-ups; CI spike PR allowed in step 3.
- step 3 stopped, 2026-11-24 12:27, user switched to the light planner mid-step; no 03 file written; spikes in spikes/ (git-ignored) kept; CI spike PR #1 closed, remote spike branch gone.
- I1 (light planner), covered by 01-research-and-stories.md + 02-alternatives.md, 2026-11-24 12:27, switched to light planner; I1 not rerun.
- I2 (light planner), 02-chosen.md, 2026-11-24 12:33, all step-3 spikes rerun (rerun_i2.sh) and CI PR #1 read; chosen: Alternative A with stdlib SQLite (S7-b), opaque cookie sessions, *.localhost per account, Recharts; falsified: signed-cookie revocation, materialised horizon, app.routes walk, Alembic batch keeping ON DELETE, Vite default host for 127.0.0.1, passlib+bcrypt5 breakage.
- I2 accepted by user, 2026-11-24 12:35, going to I3.
- I3 (light planner), 03-decisions.md + 03-solution-prd.md, 2026-11-24 12:44, 4 user decisions; PRD with 19 stories, flows, 15 tasks (bud-01..bud-15), DoD, Evals: no; open issues OI-1 (form limit route, blocks bud-10), OI-2, OI-3; 8 unconfirmed defaults in section 12.
- handoff, ~/Developing/.claude/runs/budget-app/first-version/handoff.md, 2026-11-24 12:47, planning ends here; building continues in a new session (open items OI-1..3 and section 12 defaults still to ask; plan not yet committed).
- open items, 03-decisions.md (decisions 5-8) + 03-solution-prd.md, 2026-11-24 12:55, user chose the limit-check route (OI-1), the budget-scoped split path (OI-2), in-place edit for a split at or before the rule start (OI-3), and kept all eight defaults; the architecture skill proposal was approved; architecture.md and the PRD (sections 3, 4, 5, 6, 8, 11, 12) rewritten to the current version, old copies in history/.
