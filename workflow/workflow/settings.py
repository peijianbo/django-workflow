
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-wts*jf%)m2&)fq=03g(o1*mgkxc*tdc=vgb_3zl=lg6*g-78gl'

DEBUG = True
LANGUAGE_CODE = 'zh-Hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True

INSTALLED_APPS = [
    # django内置app
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 三方app
    'rest_framework.authtoken',

    # 自己app
    'workflow.apps.user',
    'workflow.apps.workflow',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'workflow.urls'

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

WSGI_APPLICATION = 'workflow.wsgi.application'

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DEFAULT_PAGINATION_CLASS': 'workflow.libs.frameworks.pagination.CustomPageNumberPagination',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_METADATA_CLASS': 'workflow.libs.frameworks.metadata.SimpleMetadata',
}

DATABASES = {
    # 'default': {
    #         'ENGINE': 'django.db.backends.sqlite3',
    #         'NAME': BASE_DIR / 'db.sqlite3',
    #     }
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME', 'workflow'),
        'USER': os.getenv('DATABASE_USER', 'root'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'pwd123456'),
        'HOST': os.getenv('DATABASE_HOST', '127.0.0.1'),
        'PORT': os.getenv('DATABASE_PORT', 3306),
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {'charset': 'utf8mb4', 'init_command': 'SET sql_mode="STRICT_TRANS_TABLES"'},
    },
}

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

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

ALLOWED_HOSTS = ['*']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'user.User'
