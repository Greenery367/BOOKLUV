import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# =====================
# 기본 설정
# =====================
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", "local-dev-secret-key")
DEBUG = True

ALLOWED_HOSTS = ["*"]

# =====================
# Application
# =====================
INSTALLED_APPS = [
    "daphne",
    "channels",
    "corsheaders",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "klub_board",
    "klub_chat",
    "klub_talk",
    "klub_user",
    "klub_recommend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

# =====================
# WSGI / ASGI
# =====================
WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

# =====================
# Database (Postgres 우선, 없으면 SQLite)
# =====================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # 로컬 Docker Compose 환경에서 DB 컨테이너 이름은 'db'입니다.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "yourdbname",      # docker-compose.yml의 POSTGRES_DB와 일치
            "USER": "postgres",        # docker-compose.yml의 POSTGRES_USER와 일치
            "PASSWORD": "yourpassword", # docker-compose.yml의 POSTGRES_PASSWORD와 일치
            "HOST": "db",              # 'localhost'가 아니라 서비스 이름인 'db'로 수정!
            "PORT": "5432",
        }
    }

# =====================
# Redis / Channels
# =====================
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0") 

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    }
}

# Celery 설정도 REDIS_URL을 따라가므로 자동으로 해결됩니다.
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# =====================
# Static files
# =====================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# =====================
# Auth
# =====================
AUTH_USER_MODEL = "klub_user.User"

# =====================
# CORS (로컬은 전부 허용)
# =====================
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# =====================
# Timezone
# =====================
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# =====================
# Security (로컬은 최소)
# =====================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# =====================
# Celery (로컬 Redis)
# =====================
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Seoul"
CELERY_ENABLE_UTC = False

# =====================
# Logging (성능 테스트용)
# =====================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
