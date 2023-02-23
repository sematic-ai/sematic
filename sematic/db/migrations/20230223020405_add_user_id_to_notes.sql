-- migrate:up

ALTER TABLE notes ADD COLUMN user_id character(32);

UPDATE notes INNER JOIN users ON notes.author_id = users.email SET notes.user_id = users.id;

ALTER TABLE notes UPDATE COLUMN user_id character(32) NOT NULL REFERENCES users(id);

UPDATE notes DROP COLUMN author_id;

-- migrate:down

ALTER TABLE notes ADD COLUMN author_id TEXT;

UPDATE notes INNER JOIN users ON notes.user_id = users.id SET notes.author_id = users.email;

ALTER TABLE notes DROP COLUMN user_id;