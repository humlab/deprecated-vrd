#!/usr/bin/env bash

source scripts/logging_functions.sh

info "1. Deploying application with configuration settings (passwords omitted)"
debug "FLASK_ENV=${FLASK_ENV}"
debug "REACT_APP_API_URL=${REACT_APP_API_URL}"
debug "APP_SETTINGS=${APP_SETTINGS}"
debug "POSTGRESQL_HOST=${POSTGRESQL_HOST}"
debug "POSTGRESQL_PORT=${POSTGRESQL_PORT}"
debug "POSTGRES_USER=${POSTGRES_USER}"
debug "DATABASE_URL=${DATABASE_URL}"
debug "DATABASE_TEST_URL=${DATABASE_TEST_URL}"
debug "FLASK_DEBUG=${FLASK_DEBUG}"
debug "UPLOADS_DIRECTORY=${UPLOADS_DIRECTORY}"
debug "ARCHIVE_DIRECTORY=${ARCHIVE_DIRECTORY}"
debug "REDIS_URL=${REDIS_URL}"

info "2. Waiting for PostgreSQL"

while ! nc -z $POSTGRESQL_HOST $POSTGRESQL_PORT; do
  debug "2. Waiting on connection..."
  sleep 0.1
done

info "2. PostgreSQL started!"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
debug "SCRIPT_DIR=${SCRIPT_DIR}"

debug "\$FLASK_ENV=\"${FLASK_ENV}\" (can be empty)"

if [[ "$FLASK_ENV" = "development" ]]
then
  info "3. Recreating database..."
  python3 -m middleware.manage recreate_db
  info "3. Tables created..."
  info "3. Done!"
else
  info "3. Leaving database as is because ${FLASK_ENV} != \"development\"... "
fi

info "4. Loading reference archive from ${ARCHIVE_DIRECTORY}"
python3 -m middleware.manage seed_archive_videos
info "4. Done loading archive"

info "5. Loading sample query videos from ${UPLOADS_DIRECTORY}"
python3 -m middleware.manage seed_query_videos
info "5. Done loading sample query videos"

info "6. (final) Starting webserver..."
python3 -m middleware.manage run -h 0.0.0.0
