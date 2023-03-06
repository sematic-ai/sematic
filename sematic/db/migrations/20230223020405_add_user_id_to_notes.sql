-- migrate:up

CREATE TABLE notes_tmp (
    id character(32) NOT NULL,
    user_id character(32),
    note TEXT NOT NULL,
    run_id character(32) NOT NULL,
    root_id character(32) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,

    PRIMARY KEY(id),

    FOREIGN KEY(run_id) REFERENCES runs (id),
    FOREIGN KEY(root_id) REFERENCES runs (id),
    FOREIGN KEY(user_id) REFERENCES users (id)
);


INSERT INTO
    notes_tmp
    (id, user_id, note, run_id, root_id, created_at, updated_at)
SELECT 
    notes.id, users.id, notes.note, notes.run_id, notes.root_id, notes.created_at, notes.updated_at
FROM notes
JOIN users ON users.email = notes.author_id
WHERE notes.author_id != 'anonymous@acme.com';

INSERT INTO
    notes_tmp
    (id, user_id, note, run_id, root_id, created_at, updated_at)
SELECT 
    notes.id, NULL, notes.note, notes.run_id, notes.root_id, notes.created_at, notes.updated_at
FROM notes
WHERE notes.author_id = 'anonymous@acme.com';

ALTER TABLE notes RENAME TO notes_backup;

ALTER TABLE notes_tmp RENAME TO notes;

DROP TABLE notes_backup;

-- migrate:down

CREATE TABLE notes_tmp (
    id character(32) NOT NULL,
    author_id TEXT NOT NULL,
    note TEXT NOT NULL,
    run_id character(32) NOT NULL,
    root_id character(32) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,

    PRIMARY KEY(id),

    FOREIGN KEY(run_id) REFERENCES runs (id),
    FOREIGN KEY(root_id) REFERENCES runs (id)
);

INSERT INTO
    notes_tmp
    (id, author_id, note, run_id, root_id, created_at, updated_at)
SELECT 
    notes.id, users.email, notes.note, notes.run_id, notes.root_id, notes.created_at, notes.updated_at
FROM notes
JOIN users ON users.id = notes.user_id
WHERE notes.user_id IS NOT NULL;

INSERT INTO
    notes_tmp
    (id, author_id, note, run_id, root_id, created_at, updated_at)
SELECT 
    notes.id, 'anonymous@acme.com', notes.note, notes.run_id, notes.root_id, notes.created_at, notes.updated_at
FROM notes
WHERE notes.user_id IS NULL;

ALTER TABLE notes RENAME TO notes_backup;

ALTER TABLE notes_tmp RENAME TO notes;

DROP TABLE notes_backup;