# 02 Test and choose (light planner I2): budget-app / first-version

Inputs: request.md, 00-context.md (latest answers win), 01-research-and-stories.md and 02-alternatives.md (together I1's output), and the spikes from the stopped step 3. Every spike relied on here was **rerun on 2026-11-24** on this Mac (the target environment, 00-context.md: "Only on this machine"). The CI seam (S10) was read from the closed draft PR #1 on `gacuchac/simple-budgeting`; nothing was pushed.

`SP` below is `/Users/tamarmilstein/Developing/budget-app/docs/planning/first-version/spikes`. One command reruns everything: `$SP/rerun_i2.sh` (it ran end to end with exit 0 and left no listener on 8000 or 5173). Don't use `run_all.sh`: it runs `toolchain/check_web.sh` in place, and that deletes `spikes/web`, including the chart and tsdomain spike sources.

## 1. The riskiest assumption

**S1 + S2: one revocable session per made-up account, several accounts signed in at once in one Chrome, lasting until sign-out.** It scores 6, costs the most to change later (every request and the front-end API client depend on it), and it is how the user tests sharing (00-context.md: "I will be creating multiple fictitious accounts to test the data sharing").

**Result: held, with one fix.** In the installed Google Chrome (Playwright `channel: 'chrome'`, headless, with a persistent profile so a browser restart can be simulated), the opaque cookie session (S1-a):
- set `sid` as `HttpOnly`, `SameSite=Lax`, not `Secure`, 400 days, host `localhost`;
- `/api/me` returned 200 after sign-in and still 200 after Chrome was closed and reopened;
- after sign-out, `/api/me` returned 401 in the browser, and replaying the old cookie with `curl` also returned 401;
- with no cookie, `/api/me` returned 401.

Five accounts were signed in at once in **one** browser context on `localhost`, `127.0.0.1`, `alice.localhost`, `bob.localhost` and `carol.localhost`. Each host got its own `sid`, and each `/api/me` returned a different email.

**The fix:** this works only when Vite binds `server.host: '127.0.0.1'`. With Vite's default `localhost`, it listened only on `[::1]:5173`, and `http://127.0.0.1:5173` was refused (`ERR_CONNECTION_REFUSED`).

## 2. Claim results

H = held, F = falsified. "As expected" means 02-alternatives.md predicted the falsification.

### Seams
| Claim | Result | Evidence (rerun today) | Rerun |
| --- | --- | --- | --- |
| S5-a Python | H | venv from `/opt/homebrew/bin/python3.12`. pip exit 0, no "Building wheel" in the log. Python 3.12.16, SQLite 3.54.1. fastapi 0.165.0, starlette 1.10.0, pydantic 2.14.4, SQLAlchemy 2.1.9, alembic 1.20.1, pwdlib 0.4.2, argon2-cffi 25.1.0, uvicorn 0.54.0, pytest 9.2.0 | `$SP/toolchain/check_py.sh` |
| S5-a Node | H | Node v26.13.1, npm 11.20.0. `npm create vite` react-ts; installing recharts 3.11.1, chart.js 4.6.2 + react-chartjs-2 5.3.1, d3-shape 3.2.1, vitest 5.1.1 and @playwright/test 1.65.1 all exit 0 with **no ERESOLVE** and no `--legacy-peer-deps`. Also react 19.3.1, vite 8.3.8. `npm run build` exits 0 | copy `$SP/toolchain/check_web.sh` to `<tmp>/toolchain/` and run it there (as `rerun_i2.sh` does) |
| S3-a pwdlib[argon2] | H | `$argon2id$v=19$m=65536,t=3,p=4$…`. Right password True, wrong password False. Hash 23 ms + verify 23 ms (limit 500 ms). Also passes on the CI runner (S10) | `cd $SP/hashing && ../.venv/bin/python -m pytest -q -s .` |
| S3-b argon2-cffi, S3-c scrypt | H | 22+22 ms and 25+23 ms; wrong password rejected | same |
| passlib + bcrypt 5 breaks (step 1 research, counter-check) | **F** | passlib **1.9.5** with bcrypt 5.0.0 hashes and verifies fine. The research is out of date. It changes no choice: pwdlib is kept | same |
| S1-a opaque cookie, single origin through the Vite proxy | H, one sub-claim F | All browser claims held (section 1). The sub-claim "responses carry no `Access-Control-Allow-*` headers" is **falsified**: `POST /api/signin` through Vite returns `Access-Control-Allow-Origin: http://localhost:5173`. The header comes from Vite's dev-server CORS, not from the API: direct to the API there is none, and through Vite with a foreign origin there is none. So the API needs no CORS middleware | `cd $SP/session && MODE=opaque ./run.sh session && ./cors_probe.sh` |
| S1-b signed cookie (B-3) | F as expected | Replaying the cookie after sign-out returns **200**. Sign-out cannot revoke it | `cd $SP/session && MODE=signed ./run.sh session` |
| S1-c bearer in localStorage (C-4) | H | Survives the restart; replay after sign-out returns 401 | `MODE=bearer ./run.sh session` |
| S1-d `Secure` cookie on `http://localhost` | H | Chrome stores and sends it (`secure: true`); all checks the same as S1-a | `MODE=opaque SECURE=1 ./run.sh session` |
| S2-a two browser contexts (stand-in for normal + incognito windows) | H | alice and bob each see their own `/api/me` | `MODE=opaque ./run.sh two-contexts` |
| S2-b throwaway profile per account | H | alice, bob and carol all signed in at once | `MODE=opaque ./run.sh profiles` |
| S2-c `localhost` + `127.0.0.1` in one window | F with Vite's default host, H with `host: '127.0.0.1'` | Default: Vite listens on `[::1]:5173` only, so 127.0.0.1 is refused. With `127.0.0.1`: both load, and there are two separate `sid` cookies | `HOSTS=localhost,127.0.0.1 ./run.sh hosts`, then with `VHOST=127.0.0.1` |
| S2-d `*.localhost` subdomains | H (with `host: '127.0.0.1'`) | `alice.localhost`, `bob.localhost` and `carol.localhost` load with HTTP 200, with no `/etc/hosts` edit and no `allowedHosts` change. Five host-only `sid` cookies, five different users | `VHOST=127.0.0.1 HOSTS=localhost,127.0.0.1,alice.localhost,bob.localhost,carol.localhost ./run.sh hosts` |
| S8-a no signing secret | H | Opaque session: `/api/me` is 200 before and after an API restart; the rows persist | `cd $SP/session && MODE=opaque ./restart.sh` |
| S8-b secret in a git-ignored `.env` | H | 200 across a restart; the `.env` hash is unchanged (not overwritten). `.env` is already in the repo's `.gitignore` (`git check-ignore -v .env`) | `MODE=signed ./restart.sh` |
| S9-a Recharts donut + red mark + lines | H | Over-income case: the mark is at 270.0 deg (expected 270, error 0). Zero-income case: 0.0 deg (user decision: the mark sits at the income amount). 4 / 3 sectors, 2 `recharts-line-curve` paths, empty state shown, **no console errors or warnings**. 3,650 daily points render. Screenshot `$SP/charts/shot-a-over.png` | `$SP/charts/run.sh` |
| S9-b Chart.js + plugin | H | Arc starts 0/225/315 deg, plugin mark at 270 deg, the pixel at the mark is red `[208,0,0]`, no console errors | same |
| S9-c own SVG donut (d3-shape) + Recharts lines | H | Mark at 270 deg and 0 deg, no console errors | same |
| S7-b stdlib sqlite3 + `user_version` runner (and B-2) | H | `foreign_keys=1` on every connection. Deleting a category sets its entries to NULL. Deleting a budget cascades with zero orphans. 2 threads x 20 writes all commit. A fresh migration and an incremental one give the same `sqlite_master`, and rerunning changes nothing | `cd $SP/sqlite && ../.venv/bin/python -m pytest -q -s .` |
| S7-a SQLAlchemy + Alembic batch | H for PRAGMAs, FK behaviour and concurrency; **F** for "a batch migration keeps the schema" with raw-SQL or unnamed constraints | An Alembic `batch_alter_table` (recreate) over tables created from raw SQL **dropped every `ON DELETE` rule and the CHECK**. With SQLAlchemy metadata and no naming convention, ON DELETE was kept but the CHECK was dropped. Only a MetaData `naming_convention` kept both (reflect and copy_from) | same |
| S7-c database under `~/Library/Application Support/budget-app/` (`BUDGET_DB` overrides) | H | The folder is created on first use; the repo's `git status` stays clean | same |
| S7-a's in-repo `var/budget.sqlite3` | not ignored today | `git check-ignore var/budget.sqlite3` exits 1 | same |
| S4-a pydantic `EmailStr` | F as expected for made-up domains | Rejects `alice@example.test`, `bob@team.local` and `carol@demo.localhost` | `cd $SP/email && ../.venv/bin/python -m pytest -q -s .` |
| S4-b own normaliser (strip, lower-case, regex) | H | Accepts all 7 made-up forms, stored lower-cased and trimmed. Rejects `alice`, `alice@`, `@x.com`, `a b@x.com`, `alice@example` | same |
| S4-c email-validator `test_environment` | F for `.local` / `.localhost` | `.test` accepted, `bob@team.local` rejected | same |
| Invite matching (S4) | H | An invite to `ALICE2@Example.Test` made before sign-up appears for ` Alice2@example.TEST`. Accepting it makes a viewer (POST 403). A duplicate invite returns 409. A revoked invite disappears. A guessed budget id returns 404 | `cd $SP/authz && ../.venv/bin/python -m pytest -q -s .` |
| S6-a loopback binds | H, but the firewall part cannot be tested here | `127.0.0.1:8000` and `127.0.0.1:5173`, never `*:`. No address-in-use error. The macOS firewall is **disabled** on this Mac ("State = 0"), so "no firewall dialog" can't be falsified here | `$SP/ports/check.sh` |
| S10-a CI: Node 26 + `npm ci` with a lockfile made on macOS | H | Run 45448217614, `web` job: `node: v26.13.1`, `added 94 packages`, build OK, Vitest 19 passed, no `Cannot find module @rollup/rollup-linux-*` / `@esbuild/linux-*`. The Python job passes on 3.12.16 / SQLite 3.46.1 (pwdlib argon2id + FK SET NULL + WAL test) | `gh run view --job=138637756857 --repo gacuchac/simple-budgeting --log \| grep -E 'node: v\|added\|Tests '` |
| S10-b Node 24 + `npm ci`, S10-c Node 26 + `npm install` | H | Run 45448427775: both pass (v24.22.3, v26.13.1) | `gh pr checks 1 --repo gacuchac/simple-budgeting` |

### Alternatives and mechanisms
| Claim | Result | Evidence | Rerun |
| --- | --- | --- | --- |
| A-1 server-side dashboard is fast | H | Median **6.9 ms** over 20 runs (limit 200 ms): 50 rules (10,881 occurrences) + 2,000 one-offs over 5 years | `cd $SP/domain && ../.venv/bin/python -m pytest -q -s .` |
| A-2 one guard, proven by walking every budget route | H **after a fix**; the claim as written is F | Walking `app.routes` finds **no** budget routes in FastAPI 0.165, because an included `APIRouter` shows up as one private `_IncludedRouter` node (`test_app_routes_walk_is_blind_in_fastapi_0165`). Walking the **OpenAPI schema** finds 13 routes, all 404 for a non-member. An unguarded route added for the test returns 200, so the walk catches it | `cd $SP/authz && ../.venv/bin/python -m pytest -q -s .` |
| A-3 roles in the same guard | H | Viewer: GET 200, writes 403, invite 201, leave 204. The creator can't leave (409) and can delete; members then get 404. The creator revokes any invite; a viewer revokes only their own (403 otherwise). A personal budget can't be shared (409) | same |
| A-5 proxy gives one origin | H | See S1-a: no CORS needed on the API | `cd $SP/session && ./cors_probe.sh` |
| B-1 FastAPI serves the SPA and the API | H | `/` and a deep link return index.html, `/api/nope` returns a JSON 404, the hashed asset is served as JS | `cd $SP/single_origin && ../.venv/bin/python -m pytest -q .` |
| B-5 dev loop with `vite build --watch` | H | Rebuild 0.13 to 0.20 s (5 runs; the manual reload is extra) | `$SP/single_origin/devloop.sh` |
| C-1 TypeScript recurrence matches the golden table | H | Vitest 20/20 | `cd $SP/web && TZ=America/New_York npx vitest run src/tsdomain` |
| C-2 no time-zone shift | H | 20/20 under `America/New_York` and under `Pacific/Auckland` | `TZ=Pacific/Auckland npx vitest run src/tsdomain` |
| C-3 whole budget to the client | H in Node only | 237 KB JSON; recompute median 19.4 ms (Node, not Chrome) | `npx vitest run src/tsdomain/bench.test.ts` |
| D-1 a 5-year horizon covers every range | F as expected | 2031-06..12: SQL total 0, on-read total 7,000 | `cd $SP/materialise && ../.venv/bin/python -m pytest -q -s .` |
| D-2, D-3 fan-out and SQL agree | H | 1,827 rows in 1.7 ms; the split rewrote only the rows from the date onward (912 before, unchanged); SQL equals the reference | same |
| M1-a rrule with month-end forms | H | `bysetpos=-1` forms give Jan 31, Feb 28, Mar 31, Apr 30. Plain `bymonthday=31` skips Feb, Apr and Jun (the trap is real). The mapped rrule gets **no** fixture case wrong | `cd $SP/domain && ../.venv/bin/python -m pytest -q -s .` |
| M1-b own `occurrences()` | H | 17 fixture cases, plus "a split keeps the past" | same |
| M2-a calendar-aware pro-rating | H | Exactly the limit for each of the 12 full months, a full Mon–Sun week, and multi-month spans | same |
| M2-b fixed-length pro-rating | F as expected | A full February gets 45,996 of a 50,000-cent limit (0.92 x), so February would wrongly show as over | same |
| M3 donut model | H | Over: total 4,000, mark at 270 deg. Under: a "remaining" arc. Zero income: mark at 0 deg. Empty: empty state. Equal: no mark | same |
| M4 buckets and consistency | H | At most **121** points for any range up to 10 years (limit 140). The last cumulative values equal the donut totals | same |
| M6 password rules | H | `abcdefg1!` accepted; no digit, no special character and too short are each rejected | same |
| M7 seed command | H | 3 users, 4 budgets, 40 categories, 1 invite. Rerunning gives the same output. It refuses to run without an explicit DB | `cd $SP/seed && ../.venv/bin/python -m pytest -q .` |

## 3. What was falsified, and what replaces it

| Falsified | Replaced by |
| --- | --- |
| S1-b / B-3: a signed cookie can't be revoked | S1-a opaque token, stored as a SHA-256 hash in a `sessions` table. This drops Alternative B's session model |
| D-1: the fixed horizon misses later ranges | Recurrences are expanded when read (A-1: 6.9 ms). This drops Alternative D |
| A-2 as written (`app.routes` walk is blind) | The guard test walks `app.openapi()["paths"]` for `/api/budgets/{budget_id}...`. No budget-scoped route may set `include_in_schema=False`, so the walk sees every one |
| S7-a: an Alembic batch recreate drops ON DELETE and CHECK rules | Stdlib `sqlite3` with numbered `.sql` migrations and a `PRAGMA user_version` runner (S7-b, B-2: held). Table rebuilds are written by hand in the migration. A schema test asserts that `sqlite_master` still contains every `ON DELETE` and `CHECK` after all migrations |
| S2-c with Vite's default host | Vite `server.host: '127.0.0.1'`, `strictPort: true`, proxy `/api` to `http://127.0.0.1:8000` |
| S1-a sub-claim "no CORS headers" | Not a defect: the header comes from the Vite dev server. The API adds no CORS middleware |
| S4-a and S4-c reject made-up domains | S4-b own normaliser |
| M2-b (February looks over its limit) | M2-a calendar-aware pro-rating |
| passlib + bcrypt 5 breaks (research) | Nothing to replace. pwdlib is kept: it has argon2id and already ran on CI |

## 4. The choice

**Alternative A, adjusted:** a server-computed dashboard, opaque cookie sessions and two dev processes, with A's ORM layer replaced by B's stdlib SQLite layer.

Why A:
- It is the only alternative whose deciding claims all held once fixed. The arithmetic runs in pure Python, it is fast (A-1: 6.9 ms), and the user-approved rules (M1 to M4) are tested in one language.
- Isolation is enforced by one guard, and a test proves that guard covers every budget route (A-2 fixed, A-3).
- Sign-out really revokes the session (S1-a).

Why not the others:
- **B** loses on sign-out (B-3 falsified). Its single-process serving (B-1, B-5) held but isn't needed; Vite's dev server is what gives several accounts at once on `*.localhost`.
- **C** held (C-1 to C-3) but keeps the arithmetic in TypeScript while the server still validates entries. Under the roles rule it would also send a whole budget to each viewer. It brings no gain for a local POC.
- **D** failed D-1.

| Item | Chosen | Evidence it rests on |
| --- | --- | --- |
| Toolchain (S5) | S5-a: `.venv` from `/opt/homebrew/bin/python3.12`; Node 26 + npm; `package-lock.json` committed; `web/.nvmrc` = 26 | S5-a H |
| Passwords (S3, M6) | S3-a `pwdlib[argon2]`, `PasswordHash.recommended()`; rules checked on the server | S3-a H (local + CI), M6 H |
| Session (S1, S8) | S1-a: opaque 32-byte token in cookie `sid`, `HttpOnly; SameSite=Lax; Path=/; Max-Age=400 days`, no `Secure`; SHA-256 in `sessions`; sign-out deletes the row. S8-a: no signing secret | S1-a H, S8-a H |
| Several accounts (S2) | S2-d: one `*.localhost` host per account (`alice.localhost:5173`, …) in one Chrome window. Fallback: S2-b, a throwaway Chrome profile per account | S2-d H, S2-b H |
| Front-end serving (S6) | Two processes: `uvicorn --host 127.0.0.1 --port 8000`, and Vite with `host: '127.0.0.1'`, `port: 5173`, `strictPort: true`, proxy `/api` to `http://127.0.0.1:8000`. No CORS middleware | S6-a H, S2-c/S2-d fix, cors_probe |
| Database (S7) | S7-b: stdlib `sqlite3`; a connection factory sets `foreign_keys=ON`, `journal_mode=WAL` and `busy_timeout=5000`; numbered `.sql` migrations with `user_version`. Location S7-c: `~/Library/Application Support/budget-app/budget.sqlite3`, overridden by `BUDGET_DB`. Tests always use a `tmp_path` file | S7-b H, B-2 H, S7-c H; S7-a's batch trap avoided |
| Emails and invites (S4) | S4-b own normaliser; invites keyed by normalised email, status pending, accepted or revoked | S4-b H, invite matching H |
| Charts (S9) | S9-a Recharts 3 for both charts: donut `Pie` with `innerRadius`, the red overflow mark as a thin second `Pie` sliver at the M3 angle, and a `LineChart` with two cumulative series | S9-a H: mark error 0 deg, no console errors |
| CI (S10) | S10-a: Python job (3.12) plus a `web` job with `setup-node` from `web/.nvmrc` (26), `npm ci`, `npm run build`, `npx vitest run` | S10-a H on GitHub's runner |
| Recurrence (M1) | M1-b own `occurrences(rule, lo, hi)`, anchored on the rule's day with month-end clamping. An edit splits the rule at a chosen date. No runtime dependency on dateutil; an rrule cross-check may stay in the tests | M1-b H (M1-a also H) |
| Limits (M2) | M2-a calendar-aware pro-rating per limit period; rounded once | M2-a H, M2-b F |
| Donut / lines (M3, M4) | Pure `donut()` and `cumulative()`/`bucket_starts()` (≤62 days daily, ≤1 year weekly, else monthly) | M3 H, M4 H |
| Authorization (M5) | One FastAPI dependency `budget_access(need)`, which returns a typed `BudgetAccess`; repositories take `BudgetAccess`. Roles: editor (creator), viewer (invited) | A-2 (OpenAPI walk) H, A-3 H |
| Seed (M7) | `python -m <app>.seed --reset --db <path>` (or `BUDGET_DB`); refuses to run without one | M7 H |

## 5. Claims not tested

| Claim | Why not, and what is missing |
| --- | --- |
| The S6 firewall dialog never appears | The macOS application firewall is **off** on this Mac, so a dialog can't appear and the claim can't be falsified. Loopback-only binds were confirmed, and those are what keep it local |
| Visible headed-Chrome behaviour: a real quit and relaunch, incognito windows sharing one cookie jar (S2-a), a real window on `alice.localhost` | Run with Playwright and the installed Chrome, headless, with a persistent profile standing in for the quit and relaunch. A manual check in a normal window was not done |
| S2-b: the user's own Chrome profile gets no `sid` | Throwaway profiles were in temp folders; the default profile was not opened |
| S1-d `Secure` on `*.localhost` | Not needed: the chosen cookie has no `Secure` flag |
| C-3 recompute time in Chrome | Measured in Node only. Alternative C is not chosen |
| S7 concurrency through HTTP (two sessions x 20 writes via the API) | Tested at the connection level with two threads, not through uvicorn |
| B-5 full edit-to-visible time including the manual reload | Only the rebuild was timed. Alternative B is not chosen; the chosen dev loop uses Vite HMR |
| S5-b (uv) and S5-c (Node 24 locally) | Not needed, since S5-a held. Node 24 was tested only on CI (S10-b) |
| CI annotation "Node.js 20 is deprecated" for `actions/checkout@v4`, `setup-python@v5` and `setup-node@v4` | The jobs pass, because they are forced onto Node 24. Moving to newer action majors was not tested |
| Recharts mark placement at real dashboard sizes and on resize | Checked at one viewport (900x700) |

## 6. Rerun

- Everything: `$SP/rerun_i2.sh`. It runs the Python spikes one folder at a time (their `app.py` modules collide in one pytest run), runs the Node toolchain check in a temp copy, and ends by listing leftover listeners on 8000 and 5173 (expect none).
- No servers are left running: `lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8000|5173) '` printed nothing after the run.
