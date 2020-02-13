#!/usr/bin/env bash

echo "1. Deploying application with configuration settings (passwords omitted)"
echo "FLASK_ENV=${FLASK_ENV}"
echo "REACT_APP_API_URL=${REACT_APP_API_URL}"
echo "APP_SETTINGS=${APP_SETTINGS}"
echo "POSTGRESQL_HOST=${POSTGRESQL_HOST}"
echo "POSTGRESQL_PORT=${POSTGRESQL_PORT}"
echo "POSTGRES_USER=${POSTGRES_USER}"
echo "DATABASE_URL=${DATABASE_URL}"
echo "DATABASE_TEST_URL=${DATABASE_TEST_URL}"
echo "FLASK_DEBUG=${FLASK_DEBUG}"
echo "UPLOADS_DIRECTORY=${UPLOADS_DIRECTORY}"
echo "ARCHIVE_DIRECTORY=${ARCHIVE_DIRECTORY}"
echo "REDIS_URL=${REDIS_URL}"

echo "2. Waiting for PostgreSQL"

while ! nc -z $POSTGRESQL_HOST $POSTGRESQL_PORT; do
  echo "2. Waiting on connection..."
  sleep 0.1
done

echo "2. PostgreSQL started!"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "SCRIPT_DIR=${SCRIPT_DIR}"

echo "\$FLASK_ENV=\"${FLASK_ENV}\" (can be empty)"

if [[ "$FLASK_ENV" = "development" ]]
then
  echo "3. Recreating database..."
  python3 -m middleware.manage recreate_db
  echo "3. Tables created..."
  echo "3. Done!"
else
  echo "3. Leaving database as is because ${FLASK_ENV} != \"development\"... "
fi

echo "4. Loading reference archive from ${ARCHIVE_DIRECTORY}"
python3 -m middleware.manage seed_archive_videos
echo "4. Done loading archive"

echo "5. Loading sample query videos from ${UPLOADS_DIRECTORY}"
python3 -m middleware.manage seed_query_videos
echo "5. Done loading sample query videos"

echo "6. (final) Starting webserver..."
python3 -m middleware.manage run -h 0.0.0.0
