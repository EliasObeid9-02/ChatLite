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

if [ "$DEBUG" = "True" ]; then
    log "Starting Django with reload"
    uvicorn chatlite.asgi:application --host 0.0.0.0 --port 8000 --reload --reload-include "*.html" --reload-include "*.css" --reload-include "*.svg" --reload-include "*.png"
else
    log "Starting Django"
    uvicorn chatlite.asgi:application --host 0.0.0.0 --port 8000
fi
