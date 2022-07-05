pull_db_container:
	docker pull postgres:14.3

POSTGRES_CONTAINER_NAME=sematic_postgres
POSTGRES_PASSWORD=password
POSTGRES_DB_NAME=sematic

start_pg_container: pull_db_container
	docker create -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} --name ${POSTGRES_CONTAINER_NAME} -p 5432:5432 postgres:14.3

migrate_up_pg_docker:
	cd sematic; DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@0.0.0.0:5432/${POSTGRES_DB_NAME}?sslmode=disable dbmate up

migrate_down_pg_docker:
	cd sematic; DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@0.0.0.0:5432/${POSTGRES_DB_NAME}?sslmode=disable dbmate down

migrate_up_pg_aws:
	cd sematic; DATABASE_URL=${SEMATIC_OSS_DB_URL} dbmate -s db/schema.sql.pg up 

migrate_up_sqlite:
	cd sematic; DATABASE_URL="sqlite3:/${HOME}/.sematic/db.sqlite3" dbmate --schema-file db/schema.sql.sqlite up

migrate_down_sqlite:
	cd sematic; DATABASE_URL="sqlite3:/${HOME}/.sematic/db.sqlite3" dbmate -s db/schema.sql.sqlite down

clear_pg:
	psql -h 0.0.0.0 -p 5432 -d sematic < sematic/db/scripts/clear_all.sql

clear_sqlite:
	sqlite3 ~/.sematic/db.sqlite3 < sematic/db/scripts/clear_all.sql

create_pg: start_db_container db_migrate_up

pre-commit:
	flake8
	mypy sematic
	black sematic --check

refresh-dependencies:
	pip-compile --allow-unsafe requirements/requirements.in

test:
	bazel test //sematic/... --test_output=all

ui:
	cd sematic/ui; npm run build

server-image:
	docker build -t sematicai/sematic-server:dev .

start:
	cd sematic/api; docker compose up

wheel:
	rm -f bazel-bin/sematic/*.whl
	cat README.md | grep -v "<img" | grep -v "<p" > README.nohtml
	m2r --overwrite README.nohtml
	rm README.nohtml
	bazel build //sematic:wheel

test-release:
	python3 -m twine upload --repository testpypi bazel-bin/sematic/*.whl
	docker build -t sematicai/sematic-server:dev .
	docker push sematicai/sematic-server:dev

release:
	python3 -m twine upload bazel-bin/sematic/*.whl
	docker build -t sematicai/sematic-server:latest .
	docker push sematicai/sematic-server:latest