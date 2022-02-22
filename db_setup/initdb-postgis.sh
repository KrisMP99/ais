#!/bin/sh

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# https://pgtune.leopard.in.ua
max_connections = 40
shared_buffers = 975GB
effective_cache_size = 2925GB
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 500
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 6240MB
min_wal_size = 4GB
max_wal_size = 16GB

# add postgrereader user
psql -U postgres "CREATE USER aisuser WITH PASSWORD 'a401';"

# create databases
psql -U postgres "CREATE DATABASE aisdb;"

# add extensions to databases
psql gis -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql gis -c "CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;"

# restore database if dump file exists
if [ -f /srv/data/db/postgresql/backups/restore.dump ]; then
  echo "Restoring backup..."
  pg_restore -d gis --clean --if-exists /srv/data/db/postgresql/backups/restore.dump
fi