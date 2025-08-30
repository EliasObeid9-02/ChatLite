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

log "Starting Django"
daphne -b 0.0.0.0 -p 8000 chatlite.asgi:application
