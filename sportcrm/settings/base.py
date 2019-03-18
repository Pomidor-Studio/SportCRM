"""
Django settings for sportcrm project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from django.urls import reverse_lazy

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$+a*ui0^x+mdhq^$)vvl5aa+#9es)_bii00k!jqf4(_gcpmq1j'

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = False

ALLOWED_HOSTS = []

# Application definition

# Order of installed apps matters
# social_django MUST be defined BEFORE crm.apps.CrmConfig
# as we redefine social_django admin for purposes of django-reversion
INSTALLED_APPS = [
    'phonenumber_field',
    'rest_framework',
    'bootstrap_datepicker_plus',
    'bootstrap4',
    'social_django',
    'rules.apps.AutodiscoverRulesConfig',
    'reversion',
    'reversion_compare',
    'crm.apps.CrmConfig',
    'django_filters',
    'bot.apps.BotConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_select2',
    'django_tables2',
    'qr_code',
    'google_tasks.apps.GoogleTasksConfig',
    'analytical',
]

BOOTSTRAP4 = {
    'include_jquery': True,
}

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'sesame.middleware.AuthenticationMiddleware',
    'crm.middleware.SetTenantMiddleware',
    'crm.middleware.TimedAccessMiddleware',
]

ROOT_URLCONF = 'sportcrm.urls'

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

WSGI_APPLICATION = 'sportcrm.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Asia/Yekaterinburg'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DATE_INPUT_FORMATS = ['%d.%m.%Y']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler'
        }
    },
    'loggers': {
        'django_multitenant': {
            'handlers': ['null'],
            'level': 'CRITICAL'
        }
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = "/static/"

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

AUTH_USER_MODEL = 'crm.User'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.vk.VKOAuth2',
    'sesame.backends.ModelBackend',
    'rules.permissions.ObjectPermissionBackend',
    'crm.auth.backends.PhoneBackend',
    'crm.auth.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_URL = reverse_lazy('crm:accounts:login')
LOGIN_REDIRECT_URL = reverse_lazy('crm:accounts:login-redirect')
LOGOUT_REDIRECT_URL = reverse_lazy('crm:accounts:login')

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_VK_OAUTH2_KEY = ''
SOCIAL_AUTH_VK_OAUTH2_SECRET = ''

SESAME_MAX_AGE = 60 * 60 * 24 * 3  # Temporary link for coach will work 3 days

PHONENUMBER_DB_FORMAT = 'E164'
PHONENUMBER_DEFAULT_REGION = 'RU'


YANDEX_METRICA_COUNTER_ID = '52839823' # devtest metrika
YANDEX_METRICA_WEBVISOR = True

GOOGLE_ANALYTICS_JS_PROPERTY_ID = 'UA-136374884-1'

BACKGROUND_MODE: bool = False # True for run as background tasks worker
USE_GOOGLE_TASKS: bool = False


