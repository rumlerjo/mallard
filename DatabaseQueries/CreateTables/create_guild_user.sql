CREATE TABLE IF NOT EXISTS guild_users(
    user_id            INTEGER             PRIMARY KEY,
    guild_id           INTEGER             NOT NULL,
    xp                 INTEGER DEFAULT 0   NOT NULL,
    xp_needed          INTEGER DEFAULT 100 NOT NULL,
    guild_level        INTEGER DEFAULT 0   NOT NULL,
    permissions        INTEGER DEFAULT 1   NOT NULL,
    FOREIGN KEY(guild_id) REFERENCES guilds(guild_id)
);