from .base import *

DEBUG = True
SECRET_KEY = 'django-insecure-dev-key'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'supplysync_db',
        'USER': 'supplysync_user',
        'PASSWORD': 'supplysync_pass',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=supplysync,public'
        },
    }
}
