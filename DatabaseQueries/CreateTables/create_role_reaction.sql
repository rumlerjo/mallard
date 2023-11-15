CREATE TABLE IF NOT EXISTS role_reactions(
    role_id        INTEGER PRIMARY KEY,
    guild_id       INTEGER NOT NULL,
    role_name      TEXT,
    descr          TEXT,
    FOREIGN KEY(guild_id) REFERENCES guilds(guild_id)
);