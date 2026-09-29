#!/bin/sh

set -e
source ./config.sh

# get at least a template secrets/app-config.toml in place
[ -f ${SOURCE_LOCATION}/secrets/app-config.toml ] || install -o root -m 0644 ${SOURCE_LOCATION}/secrets/app-config-template.toml ${SOURCE_LOCATION}/secrets/app-config.toml
[ -f ${SOURCE_LOCATION}/secrets/rabbitmq-default-password ] || echo "rmqpass" > ${SOURCE_LOCATION}/secrets/rabbitmq-default-password
[ -f ${SOURCE_LOCATION}/secrets/elastic-initial-password ] || echo "espass" > ${SOURCE_LOCATION}/secrets/elastic-initial-password

# make sure the various data directories exist with the right ownership
install -o root -d ${DATA_PREFIX}nginx_logs
install -o ${COURSYS_USERNAME} -d ${DATA_PREFIX}submitted_files ${DATA_PREFIX}db_backups ${DATA_PREFIX}csrpt_auth ${DATA_PREFIX}dynamic_config ${DATA_PREFIX}celery_logs
install -o 1000 -d ${DATA_PREFIX}elasticsearch7

# select out compose file as the default
cd ${SOURCE_LOCATION}
ln -sf ${DOCKER_COMPOSE_FILE} compose.yml

# actually build
docker compose pull
docker compose build --pull
