CREATE TABLE IF NOT EXISTS role_reactions(
    role_id        INTEGER PRIMARY KEY,
    interaction_id INTEGER,
    guild_id       INTEGER NOT NULL,
    emoji          TEXT,
    descr          TEXT,
    FOREIGN KEY(guild_id) REFERENCES guilds(guild_id)
);