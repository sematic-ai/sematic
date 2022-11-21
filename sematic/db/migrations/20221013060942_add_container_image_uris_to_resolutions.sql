-- migrate:up

ALTER TABLE resolutions ADD COLUMN container_image_uris JSONB;

-- migrate:down

ALTER TABLE resolutions DROP COLUMN container_image_uris;
