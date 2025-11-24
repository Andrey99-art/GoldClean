# File: config/settings.py

import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.ngrok-free.app',
    '217.154.149.215',  # <--- Твой IP
    'goldclean.pl',     # <--- Твой домен (на будущее)
    'www.goldclean.pl'
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'http://217.154.149.215',  # <--- Добавь HTTP IP (для тестов)
    'https://217.154.149.215', # <--- Добавь HTTPS IP
    'https://goldclean.pl',    # <--- Домен
    'https://*.loca.lt',
    'http://*.loca.lt',
    'https://some-plums-sin.loca.lt'
]

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Сторонние приложения
    'solo',
    'django_apscheduler',

    # Наши приложения
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'products.apps.ProductsConfig',
    'orders.apps.OrdersConfig',
    'gallery.apps.GalleryConfig',
    'reviews.apps.ReviewsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
               # 'core.context_processors.site_configuration',
                'core.context_processors.site_settings', 
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# --- ЯЗЫКОВЫЕ НАСТРОЙКИ ---
LANGUAGE_CODE = 'pl'
LANGUAGES = [
    ('pl', _('Polish')),
    ('en', _('English')),
    ('ru', _('Russian')),
    ('uk', _('Ukrainian')),
]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'

# --- НАСТРОЙКИ ПОЧТЫ ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'goldclean2026@gmail.com' # Твоя почта
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD') # Пароль приложения из .env
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMIN_EMAIL = 'goldclean2026@gmail.com' # Куда приходят уведомления админу

# --- БИЗНЕС-ЛОГИКА И НАСТРОЙКИ ПЕРЕВОДА ---
VACUUM_CLEANER_PRICE = 28.00
MODELTRANSLATION_REQUIRED_LANGUAGES = ('pl', 'en', 'ru', 'uk')

# =======================================================
#          ДОБАВЛЕННАЯ НАСТРОЙКА ДЛЯ АВТОПЕРЕВОДА
# =======================================================
# Указываем, какой язык является источником для автоперевода
MODELTRANSLATION_PRIMARY_LANGUAGE = 'pl'

STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

