#!/bin/bash

set -e

wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
        sleep 0.1
    done
    echo "PostgreSQL is up!"
}

if [ -n "$POSTGRES_HOST" ]; then
    wait_for_postgres
fi

# echo "Initializing database..."
# flask db upgrade

echo "Starting Gunicorn..."
exec gunicorn backend.app:app 