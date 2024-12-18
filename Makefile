SHELL=/bin/bash

UNAME_S := $(shell uname -s)
RED := \033[0;31m
NO_COLOR := \033[1;0m
PY_VERSION := "3.12"

migrate_up_rds:
	cd sematic; DATABASE_URL=${DATABASE_URL} dbmate -s db/schema.sql.pg up 

migrate_up_sqlite:
	source .venv/bin/activate && python3 ./sematic/db/migrate.py up --verbose --env local --schema-file ${PWD}/sematic/db/schema.sql.sqlite

migrate_down_sqlite:
	source .venv/bin/activate && python3 ./sematic/db/migrate.py down --verbose --env local --schema-file ${PWD}/sematic/db/schema.sql.sqlite

clear_sqlite:
	sqlite3 ~/.sematic/db.sqlite3 < sematic/db/scripts/clear_all.sql

install-dev-deps:
	pip3 install -r requirements/ci-requirements.txt

pre-commit:
	uvx ruff format --check
	uvx ruff check --fix sematic
	uv run mypy -p sematic --disable-error-code import-untyped
	pushd sematic/ui && npm run lint && popd

fix:
	uvx ruff format
	uvx ruff check --fix --show-fixes sematic

.PHONY: py-prep
py-prep:
	uv --version || curl -LsSf https://astral.sh/uv/install.sh | sh
	rm -rf ".venv" || echo "No virtualenv yet"
	uv venv --python $(PY_VERSION)
	uv sync --extra examples --extra ray
	uv tool install --force ruff==0.8.3
	uv pip install mypy==1.13.0

.PHONY: py-sync
py-sync:
	uv sync --extra examples  --extra ray

.PHONY: update-schema
update-schema:
	source .venv/bin/activate && python3 ./sematic/db/migrate.py dump --schema-file ${PWD}/sematic/db/schema.sql.sqlite

refresh-dependencies:
	uv lock

.PHONY: ui
ui: sematic/ui/node_modules/.build_timestamp
	cd sematic/ui; npm run build

sematic/ui/node_modules/.build_timestamp: sematic/ui/package.json
	cd sematic/ui; npm install; touch -r ./package.json ./node_modules/.build_timestamp

worker-image:
	cd docker; docker build -t sematicai/sematic-worker-base:latest -f Dockerfile.worker .

sematic/ui/build:
	@$(MAKE) ui

wheel : sematic/ui/build
	rm -f bazel-bin/sematic/*.whl
	rm -f bazel-bin/sematic/ee/*.whl
	cat README.md | \
		grep -v "<img" | \
		grep -v "<p" | \
		grep -v "/p>" | \
		grep -v "<h2" | \
		grep -v "/h2>" | \
		grep -v "<h3" | \
		grep -v "/h3>" | \
		grep -v "<a" | \
		grep -v "/a>" | \
		grep -v "/img>" > README.nohtml
	bazel build //sematic:wheel

uv-wheel:
	cat README.md | \
		grep -v "<img" | \
		grep -v "<p" | \
		grep -v "/p>" | \
		grep -v "<h2" | \
		grep -v "/h2>" | \
		grep -v "<h3" | \
		grep -v "/h3>" | \
		grep -v "<a" | \
		grep -v "/a>" | \
		grep -v "/img>" > README.nohtml
	# source .venv/bin/activate && python3 -m pandoc read --format=markdown README.nohtml
	cp BUILD tmp.BUILD
	rm -rf dist build src/*.egg-info
	uvx pip wheel -w dist . && rm -rf build && mv tmp.BUILD BUILD
	rm README.nohtml

test-release:
	uvx twine check ./dist/*sematic*.whl
	uvx twine upload --repository testpypi ./dist/*sematic*.whl

release:
	uvx twine upload ./dist/*sematic*.whl

release-server:
	rm -f docker/*.whl
	cp ./dist/*sematic*.whl docker/
	cd docker; docker build --build-arg EXTRA=default -t sematic/sematic-server:${TAG} -f Dockerfile.server .
	docker push sematic/sematic-server:${TAG}
	cd docker; docker build --build-arg EXTRA=all -t sematic/sematic-server-ee:${TAG} -f Dockerfile.server .
	docker push sematic/sematic-server-ee:${TAG}

test:
	bazel test //sematic/... --test_tag_filters=nocov --test_output=all

coverage:
	bazel coverage //sematic/... --combined_report=lcov --test_tag_filters=cov --test_output=all
