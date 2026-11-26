#!/bin/sh
# NFR-08: migracijos ir demonstraciniai duomenys paleidžiant automatiškai
set -e
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py collectstatic --noinput >/dev/null
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
