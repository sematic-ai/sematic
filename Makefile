pull_db_container:
	docker pull postgres:14.3

POSTGRES_CONTAINER_NAME=sematic_postgres
POSTGRES_PASSWORD=password
POSTGRES_DB_NAME=sematic

start_pg_container: pull_db_container
	docker create -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} --name ${POSTGRES_CONTAINER_NAME} -p 5432:5432 postgres:14.3

migrate_up_pg:
	cd sematic; DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@0.0.0.0:5432/${POSTGRES_DB_NAME}?sslmode=disable dbmate up

migrate_up_sqlite:
	cd sematic; DATABASE_URL="sqlite3:/${HOME}/.sematic/db.sqlite3" dbmate --schema-file db/schema.sql.sqlite up

migrate_down_pg:
	cd sematic; DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@0.0.0.0:5432/${POSTGRES_DB_NAME}?sslmode=disable dbmate down

migrate_down_sqlite:
	cd sematic; DATABASE_URL="sqlite3:/${HOME}/.sematic/db.sqlite3" dbmate -s db/schema.sql.sqlite down

clear_pg:
	psql -h 0.0.0.0 -p 5432 -d sematic < sematic/db/scripts/clear_all.sql

clear_sqlite:
	sqlite3 ~/.sematic/db.sqlite3 < sematic/db/scripts/clear_all.sql

create_pg: start_db_container db_migrate_up

pre_commit:
	flake8
	mypy sematic
	black sematic --check

refresh_dependencies:
	pip-compile --allow-unsafe requirements/requirements.in

test:
	bazel test //sematic/... --test_output=all

build_ui:
	cd sematic/ui; npm run build

server_image: build_ui
	bazel build //sematic/api:sematic_server
	cp -f bazel-bin/sematic/api/sematic_server-0.0.1-py3-none-any.whl .
	docker build -t sematicai/sematic-server:dev .
	rm -f sematic_server-0.0.1-py3-none-any.whl

server_image_interpreter: build_server_image
	docker run -it sematic-server python3

start:
	cd sematic/api; docker compose up

wheel:
	rm -f bazel-bin/sematic/*.whl
	m2r --overwrite README.md
	bazel build //sematic:wheel

release:
	python3 -m twine upload --repository testpypi bazel-bin/sematic/*.whl