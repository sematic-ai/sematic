-- migrate:up

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

-- migrate:down

DROP TABLE users;