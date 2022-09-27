"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 3.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from email.policy import default
from pathlib import Path
from os import path
from decouple import config
from datetime import datetime, timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-#ti(4r89ts^q=#%n*v_s@$(@e(v-b*%ha!l^v2$sic7)u2ksgr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    # 'django_private_chat2.apps.DjangoPrivateChat2Config',
    'channels',
    'app.apps.AppConfig',
    'graphene_django',
    'django.contrib.admin',
    "corsheaders",
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_file_upload',
    'graphql_jwt',
    'graphql_auth',
    'graphql_jwt.refresh_token.apps.RefreshTokenConfig',
    'django_filters',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.auth0',

]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

GRAPHENE = {
    'SCHEMA': 'core.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware'
    ]
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = 'core.urls'

GRAPHQL_JWT = {
    "JWT_VERIFY_EXPIRATION": True,

    # optional
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
    "JWT_ALLOW_ANY_CLASSES": [
        "graphql_auth.mutations.Register",
    ],
}

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


AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
     'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.AllowAllUsersModelBackend',
    'graphql_auth.backends.GraphQLAuthBackend'

]


# Google Client ID :  835106107509-8maiscaaje7l2u1s4oq32je45f4lnnrd.apps.googleusercontent.com
# Client Secret key : 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

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.router.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASE_ROUTERS = ['app.models.DemoRouter']
DATABASE_APPS_MAPPING = {
    'default_db': 'default',
    'payments_db': 'payments'
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DEFAULT_DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST':config('DATABASE_HOST'),
	    'PORT':'5432'
    },
    'payments':{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('PAYMENT_DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
	    'PORT':'5432'
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# If AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are not defined,
# django-s3direct will attempt to use the EC2 instance profile instead.
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME =  config('AWS_S3_REGION_NAME')
AWS_S3_ENDPOINT_URL =  config('AWS_S3_ENDPOINT_URL')
AWS_SPLIT_LINK = AWS_S3_ENDPOINT_URL.split('//')
AWS_LINK = AWS_SPLIT_LINK[0] + '//' + AWS_STORAGE_BUCKET_NAME +'.'+ AWS_SPLIT_LINK[1]+ '/'
S3DIRECT_DESTINATIONS = {
    'primary_destination': {
        'key': 'post-videos/',
        'allowed': ['image/jpg', 'image/jpeg', 'image/png', 'image/mp4'],
    },
}

PASSWORD_HASHERS = [
  'django.contrib.auth.hashers.PBKDF2PasswordHasher',
  'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
  'django.contrib.auth.hashers.Argon2PasswordHasher',
  'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
  'django.contrib.auth.hashers.BCryptPasswordHasher',
  'django.contrib.auth.hashers.SHA1PasswordHasher',
  'django.contrib.auth.hashers.MD5PasswordHasher',
  'django.contrib.auth.hashers.UnsaltedSHA1PasswordHasher',
  'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
  'django.contrib.auth.hashers.CryptPasswordHasher',
]

# Sendgrid Settings.
SENDGRID_API_KEY = config('SENDGRID_API_KEY')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
# EMAIL_PORT = os.getenv('465')
# EMAIL_USE_TLS = os.getenv('25, 587')
# DOMAIN = os.getenv("DOMAIN")

# all-auth registraion settings
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS =1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 86400 # 1 day. This does ot prevent admin login frombeing brut forced.
ACCOUNT_LOGOUT_REDIRECT_URL ='/accounts/login/' #or any other page
LOGIN_REDIRECT_URL = '/accounts/email/' # redirects to profile page by default
ACCOUNT_PRESERVE_USERNAME_CASING = False # reduces the delays in iexact lookups
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_UNIQUE_EMAIL=True
ACCOUNT_USERNAME_MIN_LENGTH = 5
ACCOUNT_USERNAME_REQUIRED =True
ACCOUNT_USERNAME_VALIDATORS = None

ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"


ACCOUNT_FORMS = {
    'login': 'allauth.account.forms.LoginForm',
    'signup': 'allauth.account.forms.SignupForm',
    'add_email': 'allauth.account.forms.AddEmailForm',
    'change_password': 'allauth.account.forms.ChangePasswordForm',
    'set_password': 'allauth.account.forms.SetPasswordForm',
    'reset_password': 'allauth.account.forms.ResetPasswordForm',
    'reset_password_from_key': 'allauth.account.forms.ResetPasswordKeyForm',
    'disconnect': 'allauth.socialaccount.forms.DisconnectForm',
}
STRIPE_PUB_KEY = config('STRIPE_PUB_KEY')
STRIPE_SEC_KEY = config('STRIPE_SEC_KEY')

SITE_ID = 2
LOGIN_REDIRECT_URL = '/'


AUTH_USER_MODEL = 'app.User'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'