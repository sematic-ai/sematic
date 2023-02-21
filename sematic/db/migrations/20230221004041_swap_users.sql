-- migrate:up

ALTER TABLE users RENAME TO users_backup;

ALTER TABLE users_tmp RENAME TO users;

DROP TABLE users_backup;

-- migrate:down

ALTER TABLE users RENAME TO users_tmp;

CREATE TABLE users (
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    api_key TEXT NOT NULL,
    created_at timestamp NOT NULL,
    updated_at timestamp NOT NULL,

    PRIMARY KEY (email)
);