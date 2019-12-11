#!/usr/bin/env bash

echo "Waiting for PostgreSQL"

while ! nc -z db 5432; do
  echo "Waiting on connection..."
  sleep 0.1
done

echo "PostgreSQL started!"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "SCRIPT_DIR=${SCRIPT_DIR}"

if [[ "$FLASK_ENV" = "development" ]]
then
  echo "Recreating database..."
  python3 -m middleware.manage recreate_db
  echo "Tables created..."
  echo "Done!"
else
  echo "\$FLASK_ENV=\"${FLASK_ENV}\" (can be empty)"
  echo "Leaving database as is..."
fi

python3 -m middleware.manage run -h 0.0.0.0
