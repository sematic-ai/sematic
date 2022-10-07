
migrate_up_rds:
	cd sematic; DATABASE_URL=${DATABASE_URL} dbmate -s db/schema.sql.pg up 

migrate_up_sqlite:
	bazel run //sematic/db:migrate -- up --verbose --env local --schema-file ${PWD}/sematic/db/schema.sql.sqlite

migrate_down_sqlite:
	bazel run //sematic/db:migrate -- down --verbose --env local --schema-file ${PWD}/sematic/db/schema.sql.sqlite

clear_sqlite:
	sqlite3 ~/.sematic/db.sqlite3 < sematic/db/scripts/clear_all.sql

install-dev-deps:
	pip install -r requirements/ci-requirements.txt

pre-commit:
	flake8
	mypy sematic
	black sematic --check
	isort sematic --diff

fix:
	isort sematic
	black sematic

refresh-dependencies:
	pip-compile --allow-unsafe requirements/requirements.in

ui:
	cd sematic/ui; npm run build

worker-image:
	cd docker; docker build -t sematicai/sematic-worker-base:latest -f Dockerfile.worker .

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
	cd docker; docker build -t sematicai/sematic-server:${TAG} -f Dockerfile.server .
	docker push sematicai/sematic-server:${TAG}

test:
	bazel test //sematic/... --test_tag_filters=nocov --test_output=all

coverage:
	bazel coverage //sematic/... --combined_report=lcov --test_tag_filters=cov --test_output=all
