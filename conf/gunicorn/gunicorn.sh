#!/bin/bash


# Start Gunicorn processes

echo Activating Environment
source activate hs_data_services

echo Checking Admin User
python manage.py ensure_admin --username admin --password default

echo Collecting Static Files
cd /home/dsuser/hs_data_services
sudo chmod -R 757 /static
python manage.py collectstatic --noinput

echo Making Migrations
python manage.py migrate --noinput

echo Starting Gunicorn.
exec gunicorn hs_data_services.wsgi:application \
    --bind 0.0.0.0:8060 \
    --workers 3 \
    --timeout 3600
