#!/bin/bash
set -e

export PGPASSWORD=test

# Wait for Postgres

{
  while ! echo -n > /dev/tcp/db/5432;
  do
    sleep 0.1;
  done;
} 2>/dev/null

# Translation from the tasks.py which fails with an internal error relevant to the `invoke` usage
flyway migrate -q -n -url="jdbc:postgresql://db:5432/test?user=test&password=test" -locations=filesystem:data/migrations
psql -h db -U test -v ON_ERROR_STOP=1 -f data/sample_db.sql || true  # Fails on the second time
python manage.py refresh_materialized
python manage.py create_index

exec "$@"
