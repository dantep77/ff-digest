-- ff-digest SQLite schema

CREATE TABLE IF NOT EXISTS raw_pulls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pulled_at TEXT NOT NULL,           -- ISO 8601 UTC timestamp
    endpoint TEXT NOT NULL,            -- e.g. "consensus-rankings", "injuries"
    params_json TEXT NOT NULL,         -- request params, for reproducibility
    response_json TEXT NOT NULL        -- raw API response body
);

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    team_id TEXT,
    position TEXT,
    bye_week TEXT,
    page_url TEXT
);

CREATE TABLE IF NOT EXISTS experts (
    expert_id INTEGER PRIMARY KEY,
    name TEXT,
    twitter TEXT
);

CREATE TABLE IF NOT EXISTS rankings_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_id INTEGER NOT NULL REFERENCES raw_pulls(id),
    pulled_at TEXT NOT NULL,
    season TEXT NOT NULL,
    week TEXT NOT NULL,
    position TEXT NOT NULL,
    scoring TEXT NOT NULL,
    player_id INTEGER NOT NULL REFERENCES players(player_id),
    rank_ecr INTEGER,
    pos_rank TEXT,
    rank_min INTEGER,
    rank_max INTEGER,
    rank_ave REAL,
    rank_std REAL,
    tier INTEGER,
    experts_json TEXT              -- {expert_id: rank} for this player, this pull
);

CREATE INDEX IF NOT EXISTS idx_rankings_history_lookup
    ON rankings_history (season, week, position, scoring, player_id, pulled_at);

CREATE TABLE IF NOT EXISTS injuries_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_id INTEGER NOT NULL REFERENCES raw_pulls(id),
    pulled_at TEXT NOT NULL,
    player_id INTEGER NOT NULL REFERENCES players(player_id),
    status TEXT,
    status_short TEXT,
    injury_type TEXT,
    comment TEXT,
    injury_update_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_injuries_history_lookup
    ON injuries_history (player_id, pulled_at);

CREATE TABLE IF NOT EXISTS news_items (
    item_id INTEGER PRIMARY KEY,       -- FantasyPros news item id (globally unique, stable)
    player_id INTEGER,                 -- no FK: news can reference players outside our tracked pool
    title TEXT,
    link TEXT,
    category TEXT,
    impact TEXT,
    created TEXT,                      -- FantasyPros' own "created" timestamp for the story
    first_seen_pulled_at TEXT NOT NULL -- our pulled_at the first time we saw this item
);

CREATE INDEX IF NOT EXISTS idx_news_items_first_seen
    ON news_items (first_seen_pulled_at);
