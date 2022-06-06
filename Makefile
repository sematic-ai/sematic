pull_db_container:
	docker pull postgres:14.3

POSTGRES_CONTAINER_NAME=sematic_postgres
POSTGRES_PASSWORD=password
POSTGRES_DB_NAME=sematic

start_db_container: pull_db_container
	docker create -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} --name ${POSTGRES_CONTAINER_NAME} -p 5432:5432 postgres:14.3

db_migrate_up:
	cd glow; DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@0.0.0.0:5432/${POSTGRES_DB_NAME}?sslmode=disable dbmate up

db_migrate_down:
	cd glow; DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@0.0.0.0:5432/${POSTGRES_DB_NAME}?sslmode=disable dbmate down

clear_db:
	psql -h 0.0.0.0 -p 5432 -d sematic < glow/db/scripts/clear_all.sql

clear_sqlite:
	sqlite3 ~/.glow/db.sqlite3 < glow/db/scripts/clear_all.sql

create_db: start_db_container db_migrate_up

pre_commit:
	flake8
	mypy glow
	black glow --check

refresh_dependencies:
	pip-compile --allow-unsafe requirements/requirements.in

test:
	bazel test //glow/... --test_output=all

build_ui:
	#cd glow/ui; npm run build

build_server_image: build_ui
	bazel build //glow/api:sematic_server
	cp -f bazel-bin/glow/api/sematic_server-0.0.1-py3-none-any.whl .
	docker build -t sematic-server .
	rm -f sematic_server-0.0.1-py3-none-any.whl

server_image_interpreter: build_server_image
	docker run -it sematic-server python3

start:
	cd glow/api; docker compose up