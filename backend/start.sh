#!/bin/bash
# Run database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn server
gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
