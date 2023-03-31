SHELL=/bin/bash

UNAME_S := $(shell uname -s)
RED := \033[0;31m
NO_COLOR := \033[1;0m

migrate_up_rds:
	cd sematic; DATABASE_URL=${DATABASE_URL} dbmate -s db/schema.sql.pg up 

migrate_up_sqlite:
	bazel run //sematic/db:migrate -- up --verbose --env local --schema-file ${PWD}/sematic/db/schema.sql.sqlite

migrate_down_sqlite:
	bazel run //sematic/db:migrate -- down --verbose --env local --schema-file ${PWD}/sematic/db/schema.sql.sqlite

clear_sqlite:
	sqlite3 ~/.sematic/db.sqlite3 < sematic/db/scripts/clear_all.sql

install-dev-deps:
	pip3 install -r requirements/ci-requirements.txt

pre-commit:
	python3 -m flake8
	python3 -m mypy sematic
	python3 -m black sematic --check
	python3 -m isort sematic --diff --check
	pushd sematic/ui && npm run lint && popd

fix:
	isort sematic
	black sematic

.PHONY: update-schema
update-schema:
	bazel run //sematic/db:migrate -- dump --schema-file ${PWD}/sematic/db/schema.sql.sqlite

# this is not supported on Mac because some of the dependencies that need to be pulled
# do not have a release version for Mac
refresh-dependencies:
ifeq ($(UNAME_S),Linux)
	bazel run //requirements:requirements3_8.update
	bazel run //requirements:requirements3_9.update
	bazel run //requirements:requirements3_10.update
else
	echo "${RED}Refreshing dependencies should only be done from Linux${NO_COLOR}"
	exit 1
endif

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
	python3 -m m2r --overwrite README.nohtml
	rm README.nohtml
	bazel build //sematic:wheel

test-release:
	python3 -m twine check bazel-bin/sematic/*.whl
	python3 -m twine upload --repository testpypi bazel-bin/sematic/*.whl

release:
	python3 -m twine upload bazel-bin/sematic/*.whl

release-server:
	rm -f docker/*.whl
	cp bazel-bin/sematic/*.whl docker/
	cd docker; docker build --build-arg EXTRA=default -t sematic/sematic-server:${TAG} -f Dockerfile.server .
	docker push sematic/sematic-server:${TAG}
	cd docker; docker build --build-arg EXTRA=all -t sematic/sematic-server-ee:${TAG} -f Dockerfile.server .
	docker push sematic/sematic-server-ee:${TAG}

test:
	bazel test //sematic/... --test_tag_filters=nocov --test_output=all

coverage:
	bazel coverage //sematic/... --combined_report=lcov --test_tag_filters=cov --test_output=all
