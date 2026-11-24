CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    pw_hash TEXT NOT NULL
);

CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL
);

CREATE TABLE budgets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('personal','shared')),
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE memberships (
    budget_id INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('editor','viewer')),
    PRIMARY KEY (budget_id, user_id)
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('income','expense')),
    name TEXT NOT NULL,
    UNIQUE (budget_id, kind, name)
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('income','expense')),
    name TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    source TEXT,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('one_off','every','monthly_on_day')),
    start_date TEXT NOT NULL,
    end_date TEXT,
    every_n INTEGER CHECK (every_n >= 1),
    every_unit TEXT CHECK (every_unit IN ('day','week','month')),
    month_day INTEGER CHECK (month_day BETWEEN 1 AND 31),
    CHECK (source IS NULL OR kind = 'income'),
    CHECK (end_date IS NULL OR end_date >= start_date),
    CHECK (
        (rule_type = 'one_off' AND end_date IS NULL AND every_n IS NULL AND every_unit IS NULL AND month_day IS NULL)
        OR (rule_type = 'every' AND every_n IS NOT NULL AND every_unit IS NOT NULL AND month_day IS NULL)
        OR (rule_type = 'monthly_on_day' AND month_day IS NOT NULL AND every_n IS NULL AND every_unit IS NULL)
    )
);
