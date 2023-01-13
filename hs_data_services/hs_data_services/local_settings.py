"""
Django local settings for hs_data_services project.

Generated by 'django-admin startproject' using Django 3.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from dotenv import dotenv_values

config = dotenv_values(".env")

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [config.get('HYDROSHARE_DOMAIN', 'hydroshare.org'), 'gnupstream', 'localhost', '127.0.0.1']

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.get('SECRET_KEY', 'secret')

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/his/'
STATIC_ROOT = '/static/his/'

PROXY_BASE_URL = config.get('DATA_SERVICES_URL', 'http://localhost:8090/his')

# Celery settings

CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_BEAT_SCHEDULE = {}

# HydroShare Data Services Connection settings
HYDROSHARE_URL = config.get('HYDROSHARE_REST_URL', 'http://localhost:8000/hsapi')

DATA_SERVICES = {
    'geoserver': {
        'URL': config.get('GEOSERVER_REST_URL', 'http://localhost:8090/geoserver/rest'),
        'USER': config.get('GEOSERVER_USERNAME', 'admin'),
        'PASSWORD': config.get('GEOSERVER_PASSWORD', 'geoserver'),
        'IRODS_DIR': config.get('IRODS_LOCAL_DIRECTORY', '/tmp'),
        'NAMESPACE': config.get('WORKSPACE_PREFIX', 'HS')
    }
}
