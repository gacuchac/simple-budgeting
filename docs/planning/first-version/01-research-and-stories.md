# 01 Research, user stories and risk register: budget-app / first-version

Inputs: request.md, 00-context.md (including "Added after step 0": a POC, everything local, the user creates several made-up accounts to test sharing).

## 1. What the work is

A proof of concept budgeting app that runs only on this Mac. Several made-up accounts sign in with email and password; each has a private budget and can create or join shared budgets. Users enter one-off and recurring income and expenses by hand, manage expense categories and per-category limits, and see a dashboard for a chosen month or date range: a donut chart of expenses against income and line charts of income and expenses over time.

POC rigour applies throughout: correct and isolated data, tests for the logic, no production hardening. All accounts are fictitious; no real person's data is stored.

## 2. Research

### 2.1 Existing code
- `~/Developing/budget-app` is the bare workspace template (one commit, `X0: Start from the workspace project template`). It has no app code. It contains `CLAUDE.md`, `.gitignore` (already ignores `.env`, `.venv/`, `docs/planning/*/spikes/`), `requirements-dev.txt` (pytest only), `scripts/ci/check_branch_order.py` with its test, and two GitHub workflows.
- `.github/workflows/tests.yml` runs only `python -m pytest -q` on Python 3.12. It has no front-end job.
- The repo has **no git remote**. Branches are `dev`, `uat` and `main`, all local. The GitHub CI does not run, and PRs are not possible. Merges into dev have to be local `git merge --no-ff` (loop.md 4b).

### 2.2 Target environment (this Mac, checked 2026-11-24)
| Item | Found |
| --- | --- |
| OS | macOS (Darwin 24.6.0), Apple Silicon (Homebrew in /opt/homebrew) |
| Python | `/usr/bin/python3` is **3.9.6**; `/opt/homebrew/bin/python3.12` is **3.12.16** (matches CI's 3.12). No uv and no pyenv. |
| SQLite | 3.43.2 linked by the system Python, **3.54.1** linked by Homebrew Python 3.12 |
| Node / npm | Node **v26.13.1**, npm 11.20.0 (Homebrew) |
| Registries | pypi.org and registry.npmjs.org both return 200; no custom npm registry or pip config |
| Browsers | Google Chrome and Safari installed |
| Ports | 5000 and 7000 are held by `ControlCenter` (AirPlay receiver); 8787 is in use by another Python process; **8000 and 5173 are free** |

### 2.3 Web research
- **Password hashing.** passlib is unmaintained (last release 2020). bcrypt 5.0.0 (Sep 2025) raises on passwords longer than 72 bytes instead of truncating them, and that breaks passlib's bcrypt backend when it starts. pwdlib, the successor that FastAPI Users uses, hashes with Argon2 by default (`pip install 'pwdlib[argon2]'`). The plan should not depend on passlib + bcrypt.
- **Charts.** Recharts is the most common React dashboard choice: a declarative JSX API, SVG output, TypeScript types, v3 current. It has a donut (`Pie` with `innerRadius`) and multi-series `LineChart`. Chart.js through react-chartjs-2 renders to canvas and is smaller. Nivo has better-looking defaults but is larger and needs one package per chart type. No source confirmed React 19 peer compatibility for any of them on Node 26, so check that on install (S5).
- **Cookies on localhost.** Chrome (89+) and Firefox (75+) accept `Secure` cookies over `http://localhost`. **Safari rejects them**, along with `__Host-` and `__Secure-` cookie names (WebKit bugs 231035 and 232088, still open). A cookie session on plain-HTTP localhost has to leave out `Secure`, or else Safari is out.
- **Recurrence.** In dateutil, `rrule(MONTHLY, bymonthday=31)` *skips* months that have no 31st. Month-end recurrences need `bymonthday=-1`, or `bymonthday=(28,29,30,31), bysetpos=-1`. A naive "same day every month" expansion will drop payments.

### 2.4 Domain notes that shape the stories
- Money is stored as integer minor units (cents). Floats give wrong totals on the dashboard.
- A recurring entry is a rule: amount, frequency, start, optional end. The dashboard expands it into occurrences inside the chosen period. No rows are written per occurrence.
- Everything a user sees is reached through a **budget** they belong to. A personal budget has one member; a shared budget has several. Income, expenses, categories and limits belong to a budget, not to a user. Access is then one check (is this user a member of this budget?), and that check is the main correctness risk (D1 below).

## 3. User stories

Personas: **User**, any signed-in made-up account. **Member**, a user who belongs to a given shared budget. **Tester**, the person running the POC, who creates fictitious accounts to try sharing.

### Accounts
- **US-01 Sign up.** As a visitor I create an account with an email address and a password, so I get my own space. *Accepts:* made-up addresses such as `alice@example.com` are accepted, and there is no verification step. The email is stored lower-cased and must be unique. The password is stored only as a hash. A personal budget seeded with the default categories is created with the account.
- **US-02 Sign in and out.** As a user I sign in with email and password and sign out, so only I can reach my data. *Accepts:* a wrong password or unknown email gives one generic error. The session survives a page reload. Signing out ends it. Every API call without a valid session returns 401.
- **US-03 Isolation.** As a user I never see or change a budget I am not a member of. *Accepts:* requests for another budget's ids return 404 or 403. The same holds when the id is guessed.

### Entries
- **US-04 Income streams.** As a user I add, edit and delete income in the selected budget, either one-off (amount, date, name) or recurring (amount, name, frequency, start date, optional end date).
- **US-05 Expenses.** As a user I add, edit and delete expenses in the selected budget, one-off or recurring, each with a category and an optional note.

### Categories and limits
- **US-06 Categories.** As a user I see the default categories (Housing, Food, Transport, Utilities, Health, Entertainment, Other, or similar) in each budget, and I can add, rename and delete categories. *Accepts:* what happens to the expenses of a deleted category is defined (open question Q7).
- **US-07 Limits.** As a user I set or clear a spending limit for a category, and I see clearly when spending in the period exceeds it. *Accepts:* the limit period and how it maps onto a custom date range are defined (Q2).

### Dashboard
- **US-08 Period picker.** As a user I choose a month or a date range, and every figure and chart on the dashboard uses it.
- **US-09 Donut chart.** As a user I see a donut (pie with an empty centre) of the period's expenses against the period's income, split by category. *Accepts:* recurring entries count once for each occurrence in the period. An empty period shows an empty state, not an error. The composition is set by Q1.
- **US-10 Line charts.** As a user I see income and expenses over time as lines, so I can follow trends. *Accepts:* the bucket size and range are set by Q4.
- **US-11 Limit status.** As a user I see on the dashboard which categories are over their limit, or near it, in the period.

### Sharing
- **US-12 Create a shared budget.** As a user I create a named shared budget and become its first member.
- **US-13 Invite by email.** As a member I invite another user by email address. The invitation appears in the app when that user signs in, and they accept or decline it. No email is sent.
- **US-14 Switch budgets.** As a user I switch the dashboard and entry screens between my personal budget and each shared budget I belong to. *Accepts:* in a shared budget every member sees and edits all income, expenses, categories and limits.

### POC testing
- **US-15 Try sharing with made-up accounts.** As the tester I create several fictitious accounts and sign in as two of them at the same time on this Mac, so I can see one user's change appear for the other. *Accepts:* a documented way to hold two sessions at once (S2). An optional seed command that creates demo accounts and data is decided by Q11.

## 4. Out of scope
- Bank or card import, and multiple currencies (00-context.md). One currency, all entries typed by hand.
- Any deployment, hosting, public URL, DNS, TLS certificates or remote database. It runs only on this Mac.
- Real users and production hardening: password reset, email verification, MFA, OAuth or social sign-in, rate limiting, account lockout, audit logs, encryption at rest, backups.
- Sending email or any external notification. Invitations and limit warnings appear only in the app.
- External services, APIs, LLMs or paid resources. No eval cases (no LLM behaviour).
- Mobile apps, offline mode, multi-device sync, data export or import, savings goals, investments, forecasting.
- Fine-grained permissions inside a shared budget (read-only members and the like). 00-context.md says every member edits everything.

## 5. Risk register (integration seams)

Target environment: **this Mac** (00-context.md: "Only on this machine", "everything is local"). Every claim below can be tested here. There is no other environment.

Seams this work does **not** cross: external APIs, DNS, TLS certificates, hardware, cloud credentials, outbound email. The only network use at runtime is browser to API on loopback. pypi and npm are reached only when installing.

Scale: likelihood (L) and impact (I) are 1 (low) to 3 (high). Score = L x I. Cost of changing course later is low, medium or high.

| Rank | Seam | L | I | Score | Cost to change later | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | S5 Local toolchain: Python 3.12 venv, Node 26 + React + chart library | 2 | 2 | 4 | Low now, high once built on | none (foundation) |
| 2 | S3 Password hashing library | 2 | 3 | 6 | Low (one module; made-up accounts can be wiped) | S5 |
| 3 | S1 Sign-in session between browser and local API | 2 | 3 | 6 | High (every request and the front-end API client) | S5, S3 |
| 4 | S2 Two made-up accounts signed in at once on this Mac | 3 | 2 | 6 | Low (test procedure and cookie flags) | S1 |
| 5 | S7 SQLite file: foreign keys, concurrent writes, location | 2 | 2 | 4 | Medium (schema and data) | S5 |
| 6 | S4 Made-up email addresses: validation and invite matching | 2 | 2 | 4 | Low to medium (stored email format) | S1 |
| 7 | S9 Charts render in Chrome and Safari | 1 | 2 | 2 | Medium (chart components) | S5 |
| 8 | S6 Local ports and the macOS firewall prompt | 1 | 2 | 2 | Low | S5 |
| 9 | S8 Session signing secret on disk | 1 | 2 | 2 | Low | S1 |

The order is by score, then by dependency. S5 goes first because every other seam runs on it. S3, S1 and S2 form one chain (hash, then session, then two sessions at once). S7 and S4 come next, and the low-score seams last.

### S5 Local toolchain
- **Risk:** `python3` on this Mac is 3.9.6, but CI and current FastAPI expect 3.12. A venv made with the default `python3` gets the wrong interpreter and SQLite 3.43. Node 26 is newer than most packages test against, so React 19 + Vite + chart-library peer ranges may conflict.
- **Claim:** A `.venv` made with `/opt/homebrew/bin/python3.12 -m venv .venv` installs fastapi, uvicorn, pwdlib[argon2], python-dateutil and pytest, and `.venv/bin/python -m pytest -q` exits 0. In a Vite react-ts app on Node 26.13.1, `npm install` of the chosen chart library exits 0 **without** `--legacy-peer-deps`, and `npm run build` exits 0.

### S3 Password hashing
- **Risk:** passlib with bcrypt 5 fails when it starts (research 2.3). Some hashing libraries also need a compiler if no arm64 wheel exists.
- **Claim:** `pwdlib[argon2]` installs from wheels into the 3.12 venv on this Mac with no compiler step. `PasswordHash.recommended()` hashes a password, `verify` returns True for it and False for a wrong one, and each call takes under 500 ms.

### S1 Sign-in session between browser and local API
- **Risk:** the front end (Vite, port 5173) and the API (port 8000) are different origins. Cookies are scoped by host, not by port, and `localhost` and `127.0.0.1` are different hosts. Safari drops `Secure` cookies on http://localhost. Cross-origin fetches need `credentials: 'include'` together with CORS that allows credentials from an explicit origin. A token kept in localStorage avoids cookies but can be read by any script.
- **Claim:** With Vite on `http://localhost:5173` proxying `/api` to the API on `127.0.0.1:8000`, signing in sets an `HttpOnly; SameSite=Lax` session cookie with no `Secure` flag. A following `GET /api/me` from the page returns 200 with that user's email in **both Chrome and Safari**, and `GET /api/me` without the cookie returns 401.

### S2 Two made-up accounts at once
- **Risk:** one browser profile holds one cookie jar per host, so signing in as Bob in a second tab signs Alice out. The user's stated purpose, testing sharing, needs two live sessions.
- **Claim:** Two signed-in users can be live at once on `http://localhost:5173`: a normal Chrome window plus a Chrome incognito window, or Chrome plus Safari. When Alice adds an expense to a shared budget, Bob sees it after a reload, and each window's `GET /api/me` returns its own email.

### S7 SQLite file
- **Risk:** SQLite does not enforce foreign keys unless `PRAGMA foreign_keys=ON` is set on every connection. Without it, deleting a category or a budget silently leaves orphan rows. Two users writing at once can hit `database is locked` in the default journal mode. The database file must live in a git-ignored place.
- **Claim:** On SQLite 3.54.1 from python3.12, with `foreign_keys=ON` and WAL set on each connection, deleting a row that other rows reference behaves exactly as the schema declares (restricted or cascaded, never orphaned). 20 concurrent writes from two sessions all commit with no `database is locked`. `git check-ignore <db path>` prints the path.

### S4 Made-up email addresses
- **Risk:** the tester will type fictitious addresses. Strict validators (email-validator, which pydantic's `EmailStr` uses) reject special-use domains such as `.test`, `.local` and `.localhost`. Invites are matched by email, so a mismatch in case or whitespace means an invite never appears.
- **Claim:** The sign-up and invite paths accept `alice@example.com` and `Alice@Example.Test `, store them trimmed and lower-cased, and reject `alice` and `alice@`. An invite sent to `alice@example.test` appears for the account that signed up as `Alice@Example.Test`. (Counter-check: pydantic `EmailStr` rejects `alice@example.test`; if it does, the API must not use it.)

### S9 Charts in the target browsers
- **Risk:** the donut and line charts are the visible outcome. An empty period, or a period with only income, can make chart components throw or render nothing.
- **Claim:** With the chosen library (Recharts as the working assumption), a donut (`innerRadius` > 0) with one slice per category plus a "remaining income" slice, and a two-series line chart, render in Chrome and Safari on this Mac. Empty data renders the empty state with no console error.

### S6 Local ports and firewall
- **Risk:** port 5000 (Flask's default) is held by macOS AirPlay. Binding to `0.0.0.0` makes macOS ask to allow incoming connections, and exposes the app to the LAN, which goes against "everything is local".
- **Claim:** `uvicorn --host 127.0.0.1 --port 8000` and Vite on `localhost:5173` both start with no "address in use" error and no macOS firewall dialog. `lsof -nP -iTCP:8000 -sTCP:LISTEN` shows only `127.0.0.1:8000`.

### S8 Session signing secret
- **Risk:** if the key is generated fresh on each start, every restart signs everyone out. If it is committed, it leaks (low stakes for a POC, but against workspace rules).
- **Claim:** The key is read from a git-ignored `.env`, or generated once into a git-ignored file. `git check-ignore` prints that file, and a session cookie issued before an API restart is still accepted after it.

### Domain risks (not seams, listed for later steps)
- **D1 Authorization scoping.** Every query must be scoped through budget membership. One missing check exposes another user's data. This is the highest-impact correctness risk. It is testable with two made-up users and guessed ids.
- **D2 Recurrence expansion.** Month-end dates (the 31st), the end date being included or not, weekly runs across period edges, and leap years. dateutil's skip behaviour (2.3) is the known trap.
- **D3 Money.** Integer cents end to end, and formatting at the edge only.
- **D4 Limits against arbitrary ranges.** A monthly limit compared with a 10-day or 3-month range needs a rule (Q2).

## 6. What 00-context.md leaves unanswered

- **Q1 Donut composition.** Are the slices the expense categories plus a "remaining income" slice? What does it show when expenses exceed income (an "over by" marker, or expenses only)?
- **Q2 Limit period.** Is a limit monthly? For a custom range, is it pro-rated, applied per calendar month, or hidden?
- **Q3 "See when it's exceeded."** Only an over-limit marker, or also a "near limit" warning (for example at 80%)? Where: the dashboard, the entry form, or both?
- **Q4 Line charts.** Bucket size (day, week or month)? Range (the selected period, or a fixed span such as the last 12 months)? Per-bucket totals or cumulative? One chart with two lines or two charts?
- **Q5 Recurrence.** Which frequencies (weekly, every two weeks, monthly, yearly)? Month-end rule? When a recurring entry is edited, does it change the whole series or only from a date onward?
- **Q6 Income categories.** Does income get categories or sources, or only a name?
- **Q7 Deleting a category** that has expenses: block it, move them to "Uncategorised", or delete them? Is each budget's category set its own, so a shared budget gets its own seeded defaults?
- **Q8 Shared budget roles.** Can any member invite, remove members, rename or delete the budget? Can a member leave? Is there an owner?
- **Q9 Invites to an unknown email.** Does the invite wait until an account with that email signs up? Does it need accept or decline, or does it join automatically? Can it be revoked?
- **Q10 Currency.** Which single currency symbol and number format?
- **Q11 Test data.** Does the tester create the fictitious accounts by hand through sign-up, or is there a seed command for demo accounts and sample entries? May the database be wiped freely between test runs?
- **Q12 Browsers.** Chrome only, or Safari too? This affects S1 cookie flags and the S2 two-session method.
- **Q13 Repo and CI.** The repo has no GitHub remote, so the template's CI never runs. Should a remote be added, and should CI get a front-end job? Otherwise merges to dev are local and checks run only on this Mac.
- **Q14 Session and password rules.** Session length (until sign-out, or a fixed number of days)? Minimum password length for made-up accounts?

## Sources
- [Introducing pwdlib, a modern password hash helper for Python](https://polar.sh/frankie567/posts/introducing-pwdlib-a-modern-password-hash-helper-for-python)
- [FastAPI Users: password hash (pwdlib, Argon2 default)](https://fastapi-users.github.io/fastapi-users/latest/configuration/password-hash/)
- [passlib and bcrypt 5 incompatibility](https://spectral-codex.pages.dev/solutions/build-errors/passlib-bcrypt5-incompatibility/)
- [recharts vs chartjs vs nivo vs visx, 2026](https://www.pkgpulse.com/guides/recharts-vs-chartjs-vs-nivo-vs-visx-react-charting-2026)
- [LogRocket: TanStack Charts vs Recharts vs Chart.js](https://blog.logrocket.com/tanstack-charts-vs-recharts-vs-chart-js/)
- [Cookie not being set in Safari](https://flaviocopes.com/cookie-not-being-set-in-safari/)
- [WebKit bug 231035: unable to set Secure cookie on localhost without HTTPS](https://bugs.webkit.org/show_bug.cgi?id=231035)
- [WebKit bug 232088](https://bugs.webkit.org/show_bug.cgi?id=232088)
- [Expressing recurring events (dateutil rrule, P. Ganssle)](https://pganssle-talks.github.io/boston-python-rrules)
- [dateutil rrule docs](https://dateutil.readthedocs.io/en/2.8.2/rrule.html)
