"""
Django settings for locallibrary project.

Generated by 'django-admin startproject' using Django 1.11.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

### SECURITY WARNING: keep the secret key used in production secret!
with open('/home/rory/secret_key.txt') as f:
    SECRET_KEY = f.read().strip()

DEBUG = True

#######



ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'transport.apps.TransportConfig',
    'heat.apps.HeatConfig',
    'home.apps.HomeConfig',
    'electrical.apps.ElectricalConfig',
    'energyStorage.apps.EnergystorageConfig',
    'generation.apps.GenerationConfig',
    'electricHeat.apps.ElectricheatConfig',
    #'maps.apps.MapsConfig',
    'whole.apps.WholeConfig',
    #'djgeojson',
    #'django.contrib.gis',
    'leaflet',
    #'django.contrib.sites',
    'django_celery_beat',
    'django_celery_results',
    'industry.apps.IndustryConfig',
]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'locallibrary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'locallibrary.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

####This has been commented but shoud remain for production!####
with open('/home/rory/database_credentials.txt') as f:
    creds = f.read().strip().split("\n")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': creds[0],
        'USER': creds[1],
        'PASSWORD': creds[2],
        'HOST': 'localhost',
        'PORT': '',
}
}


##################################################

##DATABASES = {
##    'default': {
##        'ENGINE': 'django.db.backends.sqlite3',
##        'NAME': os.path.join(BASE_DIR, 'db_nonSpatial.sqlite3'),
##    }
## }

#import dj_database_url

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')

STATIC_URL = '/static/'

#Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGIN_REDIRECT_URL = 'home'


#For geo-django

##if os.name == 'nt':
##    import platform
##    OSGEO4W = r"C:\OSGeo4W"
##    if '64' in platform.architecture()[0]:
##        OSGEO4W += "64"
##    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
##    os.environ['OSGEO4W_ROOT'] = OSGEO4W
##    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
##    os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj"
##    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']
##
##
##SPATIALITE_LIBRARY_PATH = 'mod_spatialite'
##
##LEAFLET_CONFIG = {
##    'DEFAULT_CENTER': (56.31, -3.97),
##    'DEFAULT_ZOOM': 6,
##    }


