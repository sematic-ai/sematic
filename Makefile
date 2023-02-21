
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
	python3 -m isort sematic --diff
	pushd sematic/ui && npm run lint && popd

fix:
	isort sematic
	black sematic



# this is not supported on Mac because some of the dependencies that need to be pulled
# do not have a release version for Mac
refresh-dependencies-osx:
	[[ "$(uname -a)" != *"Linux"* ]] || ( echo "Not on Mac" && exit 1 )
	bazel run //requirements:requirements3_8_osx.update
	bazel run //requirements:requirements3_9_osx.update
	bazel run //requirements:requirements3_10_osx.update
	echo "Please be sure to update requirements on Linux as well"

refresh-dependencies-linux:
	[[ "$(uname -a)" == *"Linux"* ]] || ( echo "Not on Linux" && exit 1 )
	bazel run //requirements:requirements3_8_linux.update
	bazel run //requirements:requirements3_9_linux.update
	bazel run //requirements:requirements3_10_linux.update
	echo "Please be sure to update requirements on Mac as well"

.PHONY: ui
ui:
	cd sematic/ui; npm run build

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
