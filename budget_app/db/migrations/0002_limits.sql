CREATE TABLE limits (
    id INTEGER PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL UNIQUE REFERENCES categories(id) ON DELETE CASCADE,
    period TEXT NOT NULL CHECK (period IN ('day','week','month','year')),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0)
);
