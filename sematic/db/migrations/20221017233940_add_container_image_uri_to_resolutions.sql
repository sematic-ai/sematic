-- migrate:up

ALTER TABLE resolutions RENAME COLUMN docker_image_uri TO container_image_uri;

-- migrate:down

ALTER TABLE resolutions RENAME COLUMN container_image_uri to docker_image_uri;
