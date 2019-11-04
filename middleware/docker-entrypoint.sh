#!/usr/bin/env bash

echo "Waiting for PostgreSQL"

while ! nc -z db 5432; do
  echo "Waiting on connection..."
  sleep 0.1
done

echo "PostgreSQL started!"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "SCRIPT_DIR=${SCRIPT_DIR}"

python3 -m middleware.manage run -h 0.0.0.0
