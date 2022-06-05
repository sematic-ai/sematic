pull_db_container:
	docker pull postgres:14.3

POSTGRES_CONTAINER_NAME=sematic_postgres
POSTGRES_PASSWORD=password
POSTGRES_DB_NAME=sematic

start_db_container: pull_db_container
	docker create -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} --name ${POSTGRES_CONTAINER_NAME} postgres:14.3
	docker ps | grep ${POSTGRES_CONTAINER_NAME} || docker start ${POSTGRES_CONTAINER_NAME}

run_migrations:
	cd glow; DATABASE_URL=postgres://0.0.0.0:5432/${POSTGRES_DB_NAME}?sslmode=disable dbmate up

create_db: start_db_container run_migrations