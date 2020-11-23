#!/bin/bash


# Start Gunicorn processes

echo Activating Environment
source activate hs_data_services
cd /home/dsuser/hs_data_services

echo Making Migrations
python manage.py migrate --noinput

echo Starting Celery.
exec celery -A hs_data_services beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
