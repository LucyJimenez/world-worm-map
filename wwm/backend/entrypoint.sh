#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
MAX_ATTEMPTS=30
SLEEP_SECONDS=2

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  if python -c "import socket; socket.create_connection(('${DB_HOST}', int('${DB_PORT}')), timeout=2).close()" >/dev/null 2>&1; then
    echo "Database is reachable at ${DB_HOST}:${DB_PORT}"
    exec "$@"
  fi

  echo "Waiting for database at ${DB_HOST}:${DB_PORT} (${attempt}/${MAX_ATTEMPTS})..."
  attempt=$((attempt + 1))
  sleep "$SLEEP_SECONDS"
done

echo "Database did not become reachable in time. Exiting."
exit 1
