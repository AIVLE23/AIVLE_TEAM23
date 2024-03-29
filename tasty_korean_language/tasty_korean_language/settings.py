"""
Django settings for tasty_korean_language project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import json

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-t#3+h5pt6(hxxy6!no%9jdqevqaadnio-c0oux_s87**)!7a*4"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "community",
    "aichat",
    
    # site 설정도!
    'django.contrib.sites',

    # 설치한 라이브러리
    # 'rest_framework',
    # 'rest_framework.authtoken',
    # 'rest_framework_simplejwt',
    # 'dj_rest_auth',
    # 'dj_rest_auth.registration',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.account.models.EmailAddress',
    'allauth.socialaccount.providers.google',
]

# 사이트는 1개만 사용할 것이라고 명시
SITE_ID = 1

REST_USE_JWT = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SOCIALACCOUNT_LOGIN_ON_GET=True

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'allauth.account.middleware.AccountMiddleware',
    "accounts.middleware.BlockedMiddleware",
]

ROOT_URLCONF = "tasty_korean_language.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR/'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tasty_korean_language.wsgi.application"

import json
################################################################

# secret key 값 가져오기

with open("secrets.json", "r") as f:
  secrets = json.load(f)

CHATGPT_API_KEY = secrets["CHATGPT_API_KEY"]
ETRI_API_KEY = secrets["ETRI_API_KEY"]

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'kt-aivle-584f12b40238.json'


# Email 전송
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_HOST_USER = secrets["HOST_EMAIL"]
EMAIL_HOST_PASSWORD = secrets["EMAIL_PASSWORD"]
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

################################################################


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        'HOST': 'localhost',
        'PORT': '3306',
        'NAME': 'TKL',
        'USER': 'root',
        'PASSWORD': secrets["DB_PASSWORD"],
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'tasty_korean_language', 'static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'accounts.User'

LOGIN_REDIRECT_URL = '/'

LOGOUT_REDIRECT_URL = None 

LOGIN_URL = '/accounts/login/'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend', # 이 코드 추가!

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend', # 이 코드 추가!

    # 'allauth'와 상관없이 Django admin에서 사용자 이름으로 로그인해야 함
    #'django.contrib.auth.backends.ModelBackend',

    # 'allauth' 이메일 로그인과 같은 특정 인증 방법
    # 'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/'