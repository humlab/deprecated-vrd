#!/usr/bin/env bash

echo "Waiting for PostgreSQL"

while ! nc -z $POSTGRESQL_HOST $POSTGRESQL_PORT; do
  echo "Waiting on connection..."
  sleep 0.1
done

echo "PostgreSQL started!"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "SCRIPT_DIR=${SCRIPT_DIR}"

echo "\$FLASK_ENV=\"${FLASK_ENV}\" (can be empty)"

if [[ "$FLASK_ENV" = "development" ]]
then
  echo "Recreating database..."
  python3 -m middleware.manage recreate_db
  echo "Tables created..."
  echo "Done!"
else
  echo "Leaving database as is..."
fi

echo "Loading reference archive"
python3 -m middleware.manage seed_archive_videos

echo "Loading sample query videos"
python3 -m middleware.manage seed_query_videos

echo "Starting webserver..."
python3 -m middleware.manage run -h 0.0.0.0
