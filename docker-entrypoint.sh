#!/bin/sh

set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting server..."
exec gunicorn tickr.wsgi:application --bind 0.0.0.0:8000 "$@"
