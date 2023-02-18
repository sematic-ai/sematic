-- migrate:up

CREATE TABLE users_tmp (
    id character(32) NOT NULL,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    api_key TEXT NOT NULL,
    created_at timestamp NOT NULL,
    updated_at timestamp NOT NULL,

    PRIMARY KEY (id)
);

INSERT INTO users_tmp (
    id, email, first_name, last_name, avatar_url, api_key, created_at, updated_at
) SELECT 
    lower(hex(randomblob(16))), email, first_name, last_name, avatar_url,
    api_key, created_at, updated_at
FROM users;

ALTER TABLE users RENAME TO users_backup;

ALTER TABLE users_tmp RENAME TO users;

DROP TABLE users_backup;

-- migrate:down

CREATE TABLE users_tmp (
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    api_key TEXT NOT NULL,
    created_at timestamp NOT NULL,
    updated_at timestamp NOT NULL,

    PRIMARY KEY (email)
);

INSERT INTO users_tmp (
    email, first_name, last_name, avatar_url, api_key, created_at, updated_at
) SELECT 
    email, first_name, last_name, avatar_url,
    api_key, created_at, updated_at
FROM users;

ALTER TABLE users RENAME TO users_backup;

ALTER TABLE users_tmp RENAME TO users;

DROP TABLE users_backup;
