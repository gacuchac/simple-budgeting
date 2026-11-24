# 02 Alternatives: budget-app / first-version

Inputs: request.md, 00-context.md (including the answers to step 1's 14 open questions and the four follow-ups), 01-research-and-stories.md. Where step 1 and the answers conflict, the answers win (section 0).

Nothing is chosen in this step. Step 3 tests the claims below, and step 4 builds the alternative from what holds.

Claim ids: `A-`, `B-`, `C-`, `D-` belong to the solution alternatives, `M-` to the shared domain mechanisms, and `S<n>-` to the seams. Every claim names its test. "This Mac" is the target environment (00-context.md: "Only on this machine").

---

## 0. What the answers change since step 1

| Topic | Answer (00-context.md) | Effect on the plan |
| --- | --- | --- |
| Browsers | Chrome only | S1 no longer has to work in Safari. S2 cannot use "Chrome plus Safari". S9 is tested in Chrome only. |
| Shared budget roles | The creator edits; invited members can only view; anyone may invite; members can leave; invites can be revoked | **US-14 changes**: members do *not* all edit. Step 1's out-of-scope line "read-only members" is now **in scope**, with two roles (editor = creator, viewer = invited). The first answer said "no owners"; the follow-up ("whoever created the shared budget edits it") is the later decision and is the one used here. |
| Invites | An invite waits for an unknown email; the user accepts it on sign-in | Invites are keyed by normalised email, not by user id (S4). |
| Session and password | The session lasts until sign-out. Passwords: at least 8 characters, 1 digit, 1 special character | A persistent cookie (Chrome caps cookie lifetime at 400 days), not a browser-session cookie. Password rules are checked on the server. |
| Recurrence | Every X days, weeks or months, or a fixed day of the month. Day 31 falls back to the month's last day. An edit applies from a chosen date onward | Two rule kinds (interval and day-of-month). An edit splits the series (M1). |
| Limits | Each limit has its own period type (for example $200/week, $500/month), pro-rated to the chosen range. Only "exceeded" is shown, on the dashboard and on the entry form | Pro-rating rule needed (M2). No "near limit" state. |
| Period picker | Last X days, weeks, months or years, or a start/end calendar | US-08 gets these two modes. |
| Donut | Slices are expense categories by colour. The total is the period's income. When expenses exceed income, the total becomes total expenses and income is shown as a thick red mark on the ring | A custom overflow mark: S9 risk goes up, and M3 models the geometry. |
| Line chart | One chart, two cumulative lines (income, expenses), buckets chosen automatically from the range | M4. |
| Income | Income has a source and a category | Categories get a kind (income or expense). |
| Deleting a category | Its entries become "Uncategorized" | `ON DELETE SET NULL` on the entry's category (S7). |
| Each budget's categories | Own set per budget, seeded with defaults | Seeding happens when a budget is created. |
| Currency | USD only | Integer cents; `Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'})` at the edge. |
| Test data | Tests create made-up accounts on a throwaway database; a seed command makes demo data | M7. |
| Repo and CI | Remote `gacuchac/simple-budgeting` (public), `gacuchacbot` is a collaborator; main, dev and uat are pushed; CI gets a front-end job | A **new seam S10** (GitHub Actions). Merges into dev go through PRs. The repo is public, so nothing secret may be committed (S8). |

### Seam ranking after the answers

L = likelihood, I = impact, 1 to 3. Ranked by score, then by dependency.

| Rank | Seam | L | I | Score | Change since step 1 | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | S5 Local toolchain | 2 | 2 | 4 | none; foundation, so first | none |
| 2 | S3 Password hashing | 2 | 3 | 6 | none | S5 |
| 3 | S1 Session between Chrome and the local API | 2 | 3 | 6 | Safari dropped; "until sign-out" added | S5, S3 |
| 4 | S2 Several made-up accounts signed in at once | 3 | 2 | 6 | Chrome only, so step 1's Chrome+Safari route is gone | S1 |
| 5 | S9 Charts in Chrome, including the red overflow mark | 2 | 3 | 6 | **up from 2**: custom mark; the dashboard is the headline outcome | S5 |
| 6 | S7 SQLite file | 2 | 2 | 4 | adds SET NULL for "Uncategorized" | S5 |
| 7 | S4 Made-up emails and invite matching | 2 | 2 | 4 | invites wait for unknown emails | S1 |
| 8 | S10 GitHub Actions CI with a front-end job | 2 | 2 | 4 | **new** | S5 |
| 9 | S6 Local ports and the macOS firewall | 1 | 2 | 2 | none | S5 |
| 10 | S8 Session secret on disk | 1 | 2 | 2 | the repo is now public | S1 |

---

## 1. Solution alternatives

Fixed for all of them (00-context.md): a Python API (FastAPI), a React + TypeScript front end, a SQLite file, Chrome, local only, USD, no external services. The alternatives differ in where the budgeting logic runs, how recurring entries are stored, how the session works, how the front end is served, and the data-access layer.

### Alternative A: server-computed dashboard, ORM, server-side sessions, two processes

**Approach.**
- FastAPI on `127.0.0.1:8000`, SQLAlchemy 2.0 with Alembic migrations, SQLite in WAL mode.
- A pure Python domain package (no I/O) does recurrence expansion, the donut model, the cumulative series and limit pro-rating.
- The API returns chart-ready JSON: `GET /api/budgets/{id}/dashboard?from=&to=`.
- Sessions: an opaque random token in an `HttpOnly; SameSite=Lax` cookie. Only the token's SHA-256 is stored, in a `sessions` table. Sign-out deletes the row.
- Every budget-scoped route goes through one FastAPI dependency, `budget_access(budget_id, need)`, which returns a typed `BudgetAccess`. Repository functions take a `BudgetAccess`, never a bare id.
- Dev runs Vite on `localhost:5173` and proxies `/api` to `127.0.0.1:8000`, so the browser sees one origin. Charts: Recharts.

**Good at:** one source of truth for the arithmetic, all of it tested with pytest; isolation enforced at one point; sign-out that really revokes. **Costs:** two processes in dev; an ORM and a migration tool to learn.

| # | Assumption | Falsifiable claim | Test (step 3) |
| --- | --- | --- | --- |
| A-1 | Computing the dashboard on each request is fast enough | For a budget with 50 recurring rules and 2,000 one-off entries, the pure dashboard function for a 5-year range returns in under 200 ms (median of 20 runs) on this Mac | `spikes/domain/bench_dashboard.py` with `timeit` |
| A-2 | One dependency can guard every budget-scoped route | A test that walks `app.routes` and calls each `/api/budgets/{budget_id}/...` route as a non-member gets 404 on every route. When a spike route is added without the dependency, the same test **fails** | `spikes/authz/` (FastAPI + TestClient), `pytest -q spikes/authz` |
| A-3 | Roles fit into the same dependency | With `need="view"` and `need="edit"`: viewer GET 200, viewer POST/PUT/DELETE 403, non-member 404 on all methods, editor 2xx on all; a viewer's `POST .../invites` returns 201 (anyone may invite) | same spike |
| A-4 | SQLAlchemy 2.0 + Alembic run cleanly on SQLite | See S7-a: PRAGMAs on every connection and a batch-mode column change that keeps the data | `spikes/sqlite_orm/` |
| A-5 | The Vite proxy gives one origin, so no CORS setup is needed | See S1-a | `spikes/session/` |

### Alternative B: single process, standard-library SQLite, signed-cookie sessions

**Approach.**
- FastAPI serves the built React bundle at `/` (StaticFiles plus an SPA fallback) and the API under `/api`, all on `127.0.0.1:8000`.
- Standard-library `sqlite3` with hand-written SQL. Migrations are numbered `.sql` files applied by a small runner that tracks `PRAGMA user_version`.
- Sessions use Starlette's `SessionMiddleware`: an `itsdangerous`-signed cookie that holds the user id. It needs a secret (S8).
- The domain logic is the same pure Python package as in A. Charts: Chart.js through react-chartjs-2.

**Good at:** one process and one port, fewer dependencies, plain SQL you can read. **Costs:** no hot reload unless you also run Vite; sign-out cannot revoke a copied cookie; SQL is hand-written and hand-mapped.

| # | Assumption | Falsifiable claim | Test (step 3) |
| --- | --- | --- | --- |
| B-1 | FastAPI can serve the SPA and the API side by side | After `npm run build`, `GET /` and `GET /dashboard` (a client route, deep link) return the bundle's `index.html` with 200, `GET /api/nope` returns a JSON 404, and `GET /assets/<hashed>.js` returns 200 with a JavaScript content type | `spikes/single_origin/`, `pytest -q` with TestClient against a built stub bundle |
| B-2 | A `user_version` runner is enough for migrations | Applying migrations 1..n to an empty file and applying migration n to a file already at n-1 produce the same `sqlite_master` SQL. Running the runner again changes nothing | `spikes/sqlite_raw/test_migrations.py` |
| B-3 | A signed cookie meets "until sign-out" | With `max_age` set to 400 days, the cookie survives a Chrome restart. After sign-out, **replaying the old cookie value returns 401** (expected to be falsified: a signed cookie stays valid until it expires) | Chrome restart by hand plus `curl -b` replay; `spikes/session/b_replay.sh` |
| B-4 | Chart.js can draw the overflow mark | See S9-b | `spikes/charts/` |
| B-5 | The dev loop without Vite's server is quick enough | With `vite build --watch` and `uvicorn --reload`, a change to a `.tsx` file shows after a manual reload within 3 s (median of 5) | stopwatch in `spikes/single_origin/devloop.sh` |

### Alternative C: CRUD API, client-computed dashboard, bearer token

**Approach.**
- FastAPI only stores and returns entries, rules, categories and limits, and checks access.
- The browser expands recurrences, builds the donut and the cumulative lines, and checks limits, in TypeScript (date-fns), tested with Vitest.
- Session: an opaque bearer token in `localStorage`, sent in an `Authorization` header. There is no cookie and no CSRF surface.
- Charts: Recharts.

**Good at:** instant re-computation when the period changes, a thin API. **Costs:** the arithmetic lives in TypeScript while the server still validates entries; JavaScript `Date` time-zone traps; a token that any script on the page can read.

| # | Assumption | Falsifiable claim | Test (step 3) |
| --- | --- | --- | --- |
| C-1 | The TypeScript recurrence code is correct | A date-fns implementation produces exactly the occurrence dates in the M1 fixture table (golden JSON shared with the Python reference) | `spikes/ts_domain/`, `npx vitest run` |
| C-2 | Dates do not shift with the time zone | With `TZ=America/New_York` and `TZ=Pacific/Auckland`, stepping one day at a time from `2026-03-01` to `2026-04-30` (two DST changes) gives 61 distinct `YYYY-MM-DD` strings with no gaps or repeats | `TZ=... npx vitest run spikes/ts_domain/dst.test.ts` |
| C-3 | Sending a whole budget to the browser is cheap | 2,000 entries plus 50 rules serialise to under 500 KB of JSON, and recomputing the dashboard in Chrome for a new range takes under 50 ms | Vitest bench plus a size check |
| C-4 | A token in `localStorage` meets "until sign-out" | The token survives a Chrome restart; sign-out deletes the server row, and replaying the token afterwards returns 401 | `spikes/session/c_token.sh` plus a Chrome restart |
| C-5 | One origin per account is acceptable for testing sharing | `localStorage` is per origin, so a second tab at the same origin is the same user. Only S2-c, S2-d or S2-e give two users at once (claim tested there) | see S2 |

### Alternative D: materialised occurrences, SQL aggregates

**Approach.** Like A, except that writing a recurring rule also writes one `occurrences` row per date up to a horizon (the rule's start plus 5 years, or its end date). The dashboard and the limits become `SELECT ... GROUP BY` over one-off entries plus occurrences. An edit "from a date onward" deletes the occurrences from that date and regenerates them.

**Good at:** simple reads, and room later to edit a single occurrence (not requested). **Costs:** a horizon, a write fan-out, and two copies of the truth (the rule and its rows).

| # | Assumption | Falsifiable claim | Test (step 3) |
| --- | --- | --- | --- |
| D-1 | A fixed horizon covers every range the tester picks | For a rule starting 2026-01-01 with a 5-year horizon, the totals for the range 2031-06-01..2031-12-31 equal on-read expansion (expected to be **falsified**: the picker allows any calendar range, so the horizon must be extended lazily) | `spikes/materialise/test_horizon.py` |
| D-2 | The write fan-out is cheap | Writing a daily rule (about 1,826 rows over 5 years) commits in under 100 ms, and splitting it at a date rewrites only the rows from that date onward | same spike, `timeit` |
| D-3 | SQL aggregates agree with the reference | Per-category and per-bucket sums from SQL equal the M1 to M4 Python reference on the shared fixtures, to the cent | same spike |

### Comparison (before testing)

| Criterion | A | B | C | D |
| --- | --- | --- | --- | --- |
| Where isolation is enforced | one dependency plus typed repositories | same idea, by hand | API only (the client holds a whole budget) | as in A |
| Where the arithmetic lives | Python, pytest | Python, pytest | TypeScript, Vitest | SQL plus Python |
| Sign-out revokes | yes | no (B-3) | yes | yes |
| Several accounts at once (S2) | per host or per profile | per host or per profile | per origin or per profile | per host or per profile |
| Dev processes | 2 (Vite, uvicorn) | 1 (plus an optional watcher) | 2 | 2 |
| Main uncertainty | ORM and migration friction | session revocation, dev loop | time zones, duplicated validation | horizon |

---

## 2. Domain mechanisms shared by the alternatives

These run in Python in A, B and D, and in TypeScript in C. Each one is a pure function with a fixture table. They are not seams, but D1 to D4 from step 1 sit here, and their claims are just as testable.

### M1 Recurrence expansion (D2)
Rule kinds: **interval** (every N days, weeks or months from a start date) and **day-of-month** (every month on day D, from a start date). Both have an optional inclusive end date. An edit applies from a chosen date onward: the old rule ends the day before that date, and a new rule starts on it.

| Option | Approach | Assumption | Claim | Test |
| --- | --- | --- | --- | --- |
| M1-a | `dateutil.rrule` | rrule covers both kinds if a month-end form is used | `rrule(MONTHLY, dtstart=2026-01-31, bymonthday=(28,29,30,31), bysetpos=-1)` gives Jan 31, Feb 28, Mar 31, Apr 30, and `bymonthday=(28,29,30), bysetpos=-1` gives Jan 30, Feb 28, Mar 30. Plain `bymonthday=31` **skips** February and April (a counter-check that the trap from step 1 is real) | `spikes/domain/test_rrule.py` |
| M1-b | Own function `occurrences(rule, start, end) -> list[date]` using `calendar.monthrange`, anchored on the rule's original day (not on the previous clamped date) | A 40-line function is simpler to reason about than rrule options | It passes the same fixture table as M1-a, at least 15 cases: day 31 across all 12 months; 29 Feb 2028 yearly by "every 12 months"; every 2 weeks across both range edges; end date included; a rule starting before the range; a split at a date leaves every occurrence before it unchanged | `spikes/domain/test_occurrences.py` |

### M2 Limit pro-rating (D4)
| Option | Approach | Claim | Test |
| --- | --- | --- | --- |
| M2-a | Calendar-aware: for each calendar period the range touches, add `limit x days_in_range_in_that_period / days_in_that_period` | A monthly limit gives exactly the limit, in cents, for **every** full calendar month including February. A weekly limit gives exactly the limit for a full Monday-to-Sunday week. "Last 3 months" gives the sum of the three monthly pro-rata amounts. Rounding happens once, at the end | `spikes/domain/test_prorate.py` |
| M2-b | Fixed length: day = limit / period length (month = 365.25/12 days, week = 7, year = 365.25) | A full February gets 0.92 x the monthly limit (expected: it does, which makes M2-b show February as over its limit when it is not) | same file |

### M3 Donut model
The pure function `donut(income_cents, expenses_by_category)` returns arcs and an optional mark.
- **Claims:** the arcs sum to the ring total exactly, in cents. When expenses are at most income, the ring total is income, and an unfilled "remaining" arc is income minus expenses. When expenses exceed income, the ring total is expenses and the red mark sits at `360 x income / expenses` degrees from the start. Zero income and zero expenses give the empty state.
- **Test:** `spikes/domain/test_donut.py`.
- **Open:** where the mark goes when income is 0 and there are expenses (see the end).

### M4 Cumulative series and automatic buckets
- **Rule under test:** ranges up to 62 days use daily buckets; up to 1 year, weekly; longer, monthly.
- **Claims:** every range up to 10 years gives at most 140 points. The last cumulative income and expense values equal the donut's income and expense totals for the same range. That consistency check catches recurrences counted twice.
- **Test:** `spikes/domain/test_series.py`.

### M5 Authorization with two roles (D1)
Covered by A-2 and A-3; B, C and D reuse that test unchanged. Membership row: `(budget_id, user_id, role in {editor, viewer})`. The creator is the editor; an accepted invite makes a viewer. The personal budget has one editor and cannot be shared.

### M6 Passwords
- **Claim:** the password check accepts `abcdefg1!` and rejects `abcdefgh` (no digit), `abcdefg1` (no special character) and `ab1!` (too short).
- **Test:** `spikes/domain/test_password_rules.py`.
- It runs on the server; the front end shows the same rules as hints only.

### M7 Seed command (Q11)
- **Claim:** `python -m <app>.seed --reset --db <tmp path>` creates alice, bob and carol `@example.com`, each with a personal budget, plus one shared budget (alice editor, bob viewer, carol with a pending invite). Running it twice gives the same row counts. It refuses to run without `--db` or `BUDGET_DB` pointing at a file.
- **Test:** `spikes/seed/`.

---

## 3. Seam crossings (at least two ways per seam)

### S5 Local toolchain (rank 1)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S5-a | `/opt/homebrew/bin/python3.12 -m venv .venv` + pip with `requirements.txt` / `requirements-dev.txt`; Node 26.13.1 + npm from Homebrew; `package-lock.json` committed | Homebrew 3.12 and Node 26 stay put; all packages have arm64 wheels or are pure | `.venv/bin/pip install fastapi uvicorn sqlalchemy alembic 'pwdlib[argon2]' python-dateutil httpx pytest` exits 0 with no source build ("Building wheel" absent from the log). `.venv/bin/python -c 'import sqlite3;print(sqlite3.sqlite_version)'` prints 3.54.1. In `npm create vite@latest web -- --template react-ts`, `npm i recharts` (and separately `chart.js react-chartjs-2`) exits 0 with **no** `ERESOLVE` and without `--legacy-peer-deps`; `npm run build` exits 0 | `spikes/toolchain/check.sh` |
| S5-b | Install `uv` (Homebrew), `uv venv --python 3.12`, `uv pip sync` from a lock; Node pinned with `.nvmrc` = 26 | Adding uv is acceptable (a new tool on this Mac) | `uv pip sync` reproduces the same `pip freeze` as S5-a in under 10 s; `node -v` matches `.nvmrc` | `spikes/toolchain/check_uv.sh` (only if S5-a shows a problem; installing uv needs the user's OK) |
| S5-c | Node 24 LTS instead of 26 (Homebrew `node@24`) | Some packages lag behind Node 26 | Only needed if S5-a's `npm i` or `npm run build` fails on Node 26; same commands under `node@24` exit 0 | as above |

### S3 Password hashing (rank 2)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S3-a | `pwdlib[argon2]`, `PasswordHash.recommended()` | Maintained, with arm64 wheels for argon2-cffi | Installs from wheels; `hash` then `verify` gives True for the right password and False for a wrong one; one hash plus verify takes under 500 ms; the hash string starts with `$argon2id$` | `spikes/hashing/test_hashing.py` |
| S3-b | `argon2-cffi` directly (`PasswordHasher`) | One less layer | Same claims; `verify` raises `VerifyMismatchError` on a wrong password, which the wrapper turns into False | same file |
| S3-c | Standard library `hashlib.scrypt` (n=2^14, r=8, p=1, 16-byte salt) with `hmac.compare_digest` | OpenSSL in Homebrew 3.12 provides scrypt (checked: `hasattr(hashlib,'scrypt')` is True, OpenSSL 3.5.9); no dependency at all | Hash plus verify under 500 ms; a wrong password returns False; the stored form `scrypt$n$r$p$salt$hash` round-trips | same file |
| (rejected) | passlib + bcrypt 5 | n/a | Step 1 research: breaks at start-up with bcrypt 5. Kept only as a counter-check: `passlib.hash.bcrypt.hash('x')` raises | same file, `xfail` |

### S1 Session between Chrome and the local API (rank 3)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S1-a | Opaque 32-byte token in a cookie `sid`, `HttpOnly; SameSite=Lax; Path=/; Max-Age=34560000` (400 days), no `Secure`; SHA-256 of the token in `sessions`; Vite proxies `/api` to `http://127.0.0.1:8000` (an IP address, not `localhost`, which avoids the Node `::1` trap) | Through the proxy, Chrome treats the page and the API as one origin, so no CORS is needed | In Chrome at `http://localhost:5173`, sign-in sets `sid`; `GET /api/me` returns 200 with the email; with no cookie it returns 401. After Chrome is quit and reopened, `GET /api/me` is still 200. After sign-out, replaying the old `sid` with `curl` returns 401. The response has no `Access-Control-Allow-*` headers | `spikes/session/` (FastAPI + Vite stub); Playwright with `channel: 'chrome'` (uses the installed Chrome, no browser download) plus a manual restart check |
| S1-b | Starlette `SessionMiddleware` signed cookie, `max_age` 400 days, `https_only=False`, same proxy | Revocation is not needed for a POC | The same first two claims hold. Replay after sign-out returns **200** (expected: shows the trade-off, B-3) | same spike, `MODE=signed` |
| S1-c | Bearer token in `localStorage`, `Authorization: Bearer`, no cookie | XSS exposure is acceptable for a local POC | `GET /api/me` with the header returns 200; the token survives a Chrome restart; replay after sign-out returns 401 | same spike, `MODE=bearer` |
| S1-d | Like S1-a but with `Secure` set (Chrome only now) | Chrome treats `http://localhost` as a secure context | Chrome stores a `Secure` cookie from `http://localhost:5173` and sends it back. Also tested on `http://alice.localhost:5173` (needed by S2-d) | same spike, `SECURE=1` |

### S2 Several made-up accounts signed in at once (rank 4)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S2-a | One normal Chrome window plus one incognito window | Two users are enough | Alice (normal) and Bob (incognito) each get their own `/api/me`. A **second** incognito window shows Bob, not a third user (Chrome shares one incognito cookie jar), so this gives at most two users | Playwright: two browser contexts stand in for the windows; the incognito-sharing part is checked by hand |
| S2-b | A throwaway Chrome instance per account: `open -na "Google Chrome" --args --user-data-dir=<spikes>/chrome-<name> http://localhost:5173` | Separate user-data directories give separate cookie jars and leave the user's own profile alone | Three instances (alice, bob, carol) are signed in at once, each `/api/me` returns its own email, and the user's default Chrome profile has no `sid` cookie for localhost afterwards | `spikes/two_sessions/open_as.sh` plus a manual check |
| S2-c | Different loopback host names in one window: `localhost:5173` and `127.0.0.1:5173` | Cookies are scoped by host, so the two names have separate jars; Vite must answer on both | Signed in as Alice on one and Bob on the other, at the same time. Needs Vite `server.host: '127.0.0.1'` or `true`, and the claim checks that `localhost` still loads | Playwright, one context, two pages |
| S2-d | `*.localhost` subdomains: `alice.localhost:5173`, `bob.localhost:5173` | Chrome resolves every `*.localhost` to loopback; Vite allows `.localhost` hosts by default (its `allowedHosts` check) | Any number of accounts in one Chrome window, one subdomain each, each with its own host-only `sid`. No `/etc/hosts` edit and no `allowedHosts` change needed | Playwright with `channel: 'chrome'`, one context, three pages |
| S2-e | Per-tab session (bearer token in `sessionStorage`) | n/a | **Expected to be falsified by Q14**: the token is gone when the tab closes, so the session does not last until sign-out. Listed so the trade-off is recorded | reasoning plus a one-line Playwright check |

### S9 Charts in Chrome, with the red overflow mark (rank 5)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S9-a | Recharts 3: `PieChart` + `Pie innerRadius>0`, one `Cell` per category plus a grey "remaining" arc; the overflow mark as a second, thin `Pie` ring with one red sliver centred on the income angle (or an SVG `<line>` placed with the chart's centre and radius); `LineChart` with two `Line`s using `type="stepAfter"` | Recharts 3 accepts React 19 as a peer, and its angles start where configured (`startAngle=90`, `endAngle=-270`) | Given M3 fixtures (income 3,000 and expenses 4,000), the red mark's centre in the rendered SVG lies at 270 deg +- 1 deg clockwise from 12 o'clock. Empty data shows the empty-state text with **no console error**. The line chart draws exactly 2 `path.recharts-line-curve` elements with the M4 point count | `spikes/charts/` (Vite app) + Playwright `channel: 'chrome'`: read the DOM, take a screenshot, collect console messages |
| S9-b | Chart.js 4 + react-chartjs-2: `Doughnut` with `cutout`; the mark through an inline plugin (`afterDatasetsDraw`) drawing a thick red arc; `Line` with two datasets | Canvas output can be checked through Chart.js's own element positions | `chart.getDatasetMeta(0).data` gives arc angles matching M3 within 1 deg; the plugin's drawn angle equals `360 x income / expenses`; empty data gives no console error | same harness; the claims are read from `window.__chart` |
| S9-c | Own SVG donut (`d3-shape` `pie` + `arc`, about 60 lines of TSX) + Recharts `LineChart` for the lines | Full control of the mark costs little code | The mark angle is exact (it comes from M3), and the arcs' `d` attributes match `d3-shape` outputs from a unit test; both charts render with no console error | Vitest for geometry, Playwright for rendering |

### S7 SQLite file (rank 6)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S7-a | SQLAlchemy 2.0 engine with a `connect` event setting `foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000`; Alembic with `render_as_batch=True`; database at `var/budget.sqlite3` (to be added to `.gitignore`) | Sync endpoints run in FastAPI's thread pool; WAL plus busy_timeout absorbs contention | Every new connection reports `PRAGMA foreign_keys` = 1. Deleting a category sets its entries' `category_id` to NULL ("Uncategorized"). Deleting a budget cascades to its entries, categories, limits, memberships and invites, with zero orphans (checked by `LEFT JOIN ... IS NULL` queries). 2 threads x 20 writes through the API all commit with no `database is locked`. An Alembic batch migration that adds a NOT NULL column with a default keeps every row. `git check-ignore var/budget.sqlite3` prints the path | `spikes/sqlite_orm/`, `pytest -q` |
| S7-b | Standard-library `sqlite3` with a connection factory setting the same PRAGMAs; the `user_version` migration runner (B-2) | Hand-written SQL stays small (about 9 tables) | The same claims as S7-a, without Alembic (B-2 covers migrations) | `spikes/sqlite_raw/`, `pytest -q` |
| S7-c | Database outside the repo at `~/Library/Application Support/budget-app/budget.sqlite3` | Keeps data out of the working tree entirely | The app creates the folder on first start, and `git status` in the repo stays clean after a run. The test database is always a `tmp_path` file, never this one | same spike, env var `BUDGET_DB` |

### S4 Made-up emails and invite matching (rank 7)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S4-a | pydantic `EmailStr` (email-validator), with the value normalised after validation | The tester uses ordinary-looking domains | `alice@example.com` and ` Alice@Example.COM ` are accepted and stored as `alice@example.com`. `alice@example.test` is **rejected** (expected, as email-validator rejects special-use domains by default), which would surprise a tester | `spikes/email/test_email.py` |
| S4-b | Own normaliser: strip, lower-case, then `^[^@\s]+@[^@\s]+\.[^@\s]+$` | Format checking is enough for fictitious accounts; there is no delivery | It accepts `alice@example.com`, ` Alice@Example.Test `, `bob@team.local`; rejects `alice`, `alice@`, `@x.com`, `a b@x.com`; normalises all accepted forms to lower case without surrounding spaces | same file |
| S4-c | email-validator with `test_environment=True` and `check_deliverability=False` | Allowing only `.test` is enough | `alice@example.test` is accepted; `bob@team.local` is still rejected | same file |
| invite matching (any option) | `invites(budget_id, email_normalised, invited_by, status)`; on sign-up and sign-in, pending invites for the user's normalised email are listed | n/a | An invite to `ALICE@example.com` made **before** Alice signs up appears after she signs up as `alice@example.com`. Accepting it makes her a viewer. A revoked invite no longer appears. A second invite to the same email for the same budget returns 409 | `spikes/authz/test_invites.py` (with A-2) |

### S10 GitHub Actions CI with a front-end job (rank 8)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S10-a | Extend `tests.yml`: the Python job installs `requirements.txt` + `requirements-dev.txt`; a new `web` job uses `actions/setup-node` with `node-version-file: web/.nvmrc` (26), `npm ci`, `npm run build`, `npx vitest run` | Node 26 is available to `setup-node` on `ubuntu-latest`. A lockfile generated on macOS arm64 installs on Linux x64 (the npm optional-dependency bug that dropped `@rollup/rollup-linux-x64-gnu` and similar is fixed in npm 11) | On a draft PR from a spike branch into `dev`, both jobs pass, `setup-node` logs `v26.x`, and `npm ci` logs no `Cannot find module @rollup/rollup-linux-*` or `@esbuild/linux-*` error | Needs a push to `gacuchac/simple-budgeting` and a draft PR (**needs the user's go in step 3**); with no Docker or `act` on this Mac, it cannot be simulated locally |
| S10-b | Same job with Node pinned to 24 LTS in both `.nvmrc` and CI | Pinning a version that is older than local Node avoids surprises | Same pass criteria with `v24.x` logged; locally `node@24` also builds (S5-c) | same draft PR, second commit |
| S10-c | Commit only `package.json`, and use `npm install` in CI instead of `npm ci` | Avoids lockfile platform issues | CI passes, but two runs a day apart may resolve different versions. Kept as a fallback only | same draft PR |

The `branch-order` workflow already allows `feature/*` into `dev`. A spike PR must use a `feature/` name and be closed without merging.

### S6 Local ports and the macOS firewall (rank 9)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S6-a | Two processes: `uvicorn --host 127.0.0.1 --port 8000` and Vite with `server.host: '127.0.0.1'` (or `localhost` plus the S2 host choice), `strictPort: true`, port 5173 | Loopback binds trigger no firewall dialog | Both start without "address in use". No macOS "accept incoming connections" dialog appears. `lsof -nP -iTCP -sTCP:LISTEN \| grep -E ':(8000\|5173)'` lists only `127.0.0.1` or `[::1]`, never `*:` | `spikes/ports/check.sh` plus watching for the dialog |
| S6-b | One process (Alternative B): uvicorn on `127.0.0.1:8000` serves everything | n/a | The same `lsof` claim for port 8000 only. Port 5173 is unused | same script |

### S8 Session secret on disk (rank 10)
| Option | Approach | Assumptions | Claim | Test |
| --- | --- | --- | --- | --- |
| S8-a | No signing secret at all: server-side sessions (S1-a or S1-c) store only token hashes | Random tokens in the database need no key | Repo-wide `git grep -nE '(SECRET\|secret_key)\s*='` finds nothing. Sessions survive an API restart, because the rows persist | `spikes/session/` restart test |
| S8-b | `SESSION_SECRET` in a git-ignored `.env`, created by a setup script when missing (`secrets.token_urlsafe(32)`) | `.env` is already in `.gitignore` | `git check-ignore .env` prints `.env`. A cookie issued before an API restart is accepted after it. The setup script does not overwrite an existing `.env` | same spike, `MODE=signed` |

---

## 4. Step 3 test order

In seam rank order, then the domain claims (they need only S5). Spikes go in `spikes/` (git-ignored). Each claim gets held or falsified, the evidence and a rerun command in 03-claim-tests.md.

1. S5-a (blocks everything). S5-b and S5-c only if S5-a fails; uv needs the user's OK.
2. S3-a, S3-b, S3-c, plus the passlib counter-check.
3. S1-a to S1-d, then S8-a and S8-b in the same spike.
4. S2-a to S2-d (S2-e by reasoning).
5. S9-a to S9-c, using the M3 and M4 fixtures.
6. S7-a to S7-c, B-2.
7. S4-a to S4-c and invite matching, with A-2 and A-3.
8. M1 to M7, A-1, C-1 to C-3, D-1 to D-3, B-1, B-5.
9. S6-a and S6-b.
10. S10-a to S10-c: **untested unless the user agrees** to a spike branch and a draft PR on the public repo.

Manual parts (Chrome restart in S1-a/C-4, the firewall dialog in S6, incognito sharing in S2-a) are recorded with what was observed and when.

---

## 5. Questions these alternatives raise

- **Q-a Zero income.** When a period has expenses but no income, where does the red mark go: at the 12 o'clock start (0 deg), or is it left out, with "No income" in the centre?
- **Q-b Creator leaving.** Can the creator of a shared budget leave or delete it? Who can revoke an invite: whoever sent it, the creator, or both?
- **Q-c Income categories.** Does each budget get its own seeded income categories (for example Salary, Freelance, Other), and is "source" a free-text name on each income stream?
- **Q-d Viewers and limits.** Do view-only members see limits and "exceeded" warnings? (Assumed yes.)
- **Q-e CI spike.** May step 3 push a `feature/` spike branch and open a draft PR on `gacuchac/simple-budgeting` to test S10? Without it, S10 stays untested until the first real PR.

## Sources
- [email-validator (special-use domains, test_environment)](https://pypi.org/project/email-validator)
- [email-validator source, 2.2.0](https://sources.debian.org/src/python-email-validator/2.2.0-1/email_validator/__init__.py)
- [Vite server options (host, DNS result order, allowedHosts)](https://vite.dev/config/server-options)
- [Node 17+ localhost resolves to ::1 (ECONNREFUSED)](https://serebrov.github.io/html/2023-07-28-node-econnrefused-localhost.html)
- Step 1 sources (pwdlib, passlib/bcrypt 5, Recharts/Chart.js comparisons, WebKit Secure-cookie bugs, dateutil rrule) are listed in 01-research-and-stories.md.
