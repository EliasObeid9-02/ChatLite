#!/bin/sh
set -e  # Exit on any error

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Django project initialization"

log "Running database migrations"
python manage.py migrate --noinput

log "Collecting static files"
python manage.py collectstatic --noinput --clear

exec "$@"
