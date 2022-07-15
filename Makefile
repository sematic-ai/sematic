
migrate_up_rds:
	cd sematic; DATABASE_URL=${DATABASE_URL} dbmate -s db/schema.sql.pg up 

migrate_up_sqlite:
	cd sematic; DATABASE_URL="sqlite3:/${HOME}/.sematic/db.sqlite3" dbmate --schema-file db/schema.sql.sqlite up

migrate_down_sqlite:
	cd sematic; DATABASE_URL="sqlite3:/${HOME}/.sematic/db.sqlite3" dbmate -s db/schema.sql.sqlite down

clear_sqlite:
	sqlite3 ~/.sematic/db.sqlite3 < sematic/db/scripts/clear_all.sql

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

release:
	python3 -m twine upload bazel-bin/sematic/*.whl

release-server:
	docker build -t sematicai/sematic-server:${TAG} .
	docker push sematicai/sematic-server:${TAG}