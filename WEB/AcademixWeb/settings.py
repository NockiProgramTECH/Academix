"""
Django settings for AcademixWeb project.
"""
import pymysql
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

import cloudinary
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIRS = BASE_DIR / "templates"

# ──────────────────────────────────────────────
# SÉCURITÉ
# ──────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-tkrj)2zz3^snhm8!y+xrr$=c9_uf=ad9=_m*ur(%vsn5lhzbmm')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ["*"]

# ──────────────────────────────────────────────
# CLOUDINARY — initialisation explicite
# ──────────────────────────────────────────────
cloudinary.config(
    cloud_name = os.getenv('CLOUD_NAME'),
    api_key    = os.getenv('API_KEY'),
    api_secret = os.getenv('API_SECRET'),
    secure     = True
)

# ── CORRECTIF RESOURCE_TYPE ──────────────────────────────────────────────────
# ERREUR ORIGINALE : 'RESOURCE_TYPES' (pluriel) → clé ignorée par
# django-cloudinary-storage. Le backend utilisait alors 'image' par défaut,
# ce qui faisait rejeter les PDF et DOCX par Cloudinary (retour 400/500).
#
# CORRECTION : 'RESOURCE_TYPE' (singulier) + valeur 'auto'.
# Avec 'auto', Cloudinary détecte lui-même si le fichier est une image,
# une vidéo ou un fichier brut (raw = PDF, DOCX, etc.).
# ─────────────────────────────────────────────────────────────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME':    os.getenv('CLOUD_NAME'),
    'API_KEY':       os.getenv('API_KEY'),
    'API_SECRET':    os.getenv('API_SECRET'),
    'RESOURCE_TYPE': 'auto',   # ← CORRECTIF : était 'RESOURCE_TYPES' (ignoré)
}

# ──────────────────────────────────────────────
# STOCKAGE DES FICHIERS MEDIA → CLOUDINARY
# ──────────────────────────────────────────────
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ──────────────────────────────────────────────
# APPLICATIONS
# ──────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',           # ← AVANT django.contrib.staticfiles
    'django.contrib.staticfiles',
    'cloudinary',                   # ← APRÈS staticfiles
    'Inscriptions',
    'ProfManager',
    'ParentsManager',
]

# ──────────────────────────────────────────────
# BASE DE DONNÉES — Aiven MySQL
# ──────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':     os.getenv('DB_NAME'),
        'USER':     os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST':     os.getenv('DB_HOST'),
        'PORT':     os.getenv('DB_PORT'),
        'OPTIONS': {
            'ssl': {'ca': None},
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AcademixWeb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIRS],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AcademixWeb.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'