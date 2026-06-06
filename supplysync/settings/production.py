from .base import *
import os

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'supplysync_db'),
        'USER': os.environ.get('DB_USER', 'supplysync_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'supplysync_pass'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'options': '-c search_path=supplysync,public'
        },
    }
}
