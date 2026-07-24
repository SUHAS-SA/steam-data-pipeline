-- =============================================================================
-- Steam Data Extraction & Storage Schema (V3)
-- Database: PostgreSQL
-- Description: Relational schema for Steam catalog, genres, tags, and hardware specs.
-- =============================================================================

-- Drop tables if re-initialization is needed (Order respects Foreign Key dependencies)
-- DROP TABLE IF EXISTS game_requirements CASCADE;
-- DROP TABLE IF EXISTS game_tags CASCADE;
-- DROP TABLE IF EXISTS game_genres CASCADE;
-- DROP TABLE IF EXISTS tags CASCADE;
-- DROP TABLE IF EXISTS genres CASCADE;
-- DROP TABLE IF EXISTS games CASCADE;

-- 1. Main Games Catalog Table
CREATE TABLE IF NOT EXISTS games (
    steam_appid       INT PRIMARY KEY,
    name              VARCHAR(255) NOT NULL,
    developer         TEXT,
    publisher         TEXT,
    release_date      DATE,
    platforms         TEXT,                 -- e.g. "windows, mac, linux"
    header_image      TEXT,
    metacritic_score  INT,
    about_the_game    TEXT,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Genres Lookup Table
CREATE TABLE IF NOT EXISTS genres (
    genre_id          SERIAL PRIMARY KEY,
    name              VARCHAR(100) UNIQUE NOT NULL
);

-- 3. Tags / Categories Lookup Table
CREATE TABLE IF NOT EXISTS tags (
    tag_id            SERIAL PRIMARY KEY,
    name              VARCHAR(100) UNIQUE NOT NULL
);

-- 4. Junction Table: Games <-> Genres (Many-to-Many)
CREATE TABLE IF NOT EXISTS game_genres (
    game_appid        INT REFERENCES games(steam_appid) ON DELETE CASCADE,
    genre_id          INT REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (game_appid, genre_id)
);

-- 5. Junction Table: Games <-> Tags (Many-to-Many)
CREATE TABLE IF NOT EXISTS game_tags (
    game_appid        INT REFERENCES games(steam_appid) ON DELETE CASCADE,
    tag_id            INT REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (game_appid, tag_id)
);

-- 6. System Requirements Table (Parsed Hardware Specs per Platform & Level)
CREATE TABLE IF NOT EXISTS game_requirements (
    requirement_id    SERIAL PRIMARY KEY,
    game_appid        INT REFERENCES games(steam_appid) ON DELETE CASCADE,
    platform          VARCHAR(10) NOT NULL,   -- 'pc', 'mac', 'linux'
    req_type          VARCHAR(15) NOT NULL,   -- 'minimum', 'recommended'
    os                TEXT,
    processor         TEXT,
    memory            TEXT,
    graphics          TEXT,
    directx           TEXT,
    network           TEXT,
    storage           TEXT,
    sound_card        TEXT,
    raw_requirement   TEXT,
    additional_notes  TEXT,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_game_req UNIQUE (game_appid, platform, req_type)
);

-- =============================================================================
-- Performance Optimization Indexes
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_games_release_date ON games(release_date);
CREATE INDEX IF NOT EXISTS idx_games_metacritic ON games(metacritic_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_game_req_platform ON game_requirements(platform, req_type);
CREATE INDEX IF NOT EXISTS idx_game_genres_genre_id ON game_genres(genre_id);
CREATE INDEX IF NOT EXISTS idx_game_tags_tag_id ON game_tags(tag_id);
