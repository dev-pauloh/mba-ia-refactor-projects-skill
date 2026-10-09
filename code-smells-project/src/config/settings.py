import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes")


def _env_list(name):
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


def _secret(name):
    value = os.environ.get(name)
    if not value:
        logger.warning("%s não definida; usando valor aleatório (apenas desenvolvimento)", name)
        value = secrets.token_hex(32)
    return value


class Settings:
    SECRET_KEY = _secret("SECRET_KEY")
    DEBUG = _env_bool("FLASK_DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = _env_list("CORS_ORIGINS")
    TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "3600"))
    ENABLE_ADMIN_SQL = _env_bool("ENABLE_ADMIN_SQL", False)
