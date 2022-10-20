-- migrate:up

ALTER TABLE runs ADD COLUMN container_image_uri TEXT;

-- migrate:down

ALTER TABLE runs DROP COLUMN container_image_uri;
