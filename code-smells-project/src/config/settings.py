import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes")


def _env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def _secret(name):
    value = os.environ.get(name)
    if not value:
        logger.warning("%s não definida; usando valor aleatório (apenas desenvolvimento)", name)
        value = secrets.token_hex(32)
    return value


class Settings:
    """Configuração lida do ambiente no momento da criação da aplicação."""

    def __init__(self):
        self.SECRET_KEY = _secret("SECRET_KEY")
        self.DEBUG = _env_bool("FLASK_DEBUG", False)
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.APP_ENV = os.environ.get("APP_ENV", "development")
        self.DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = _env_list("CORS_ORIGINS")
        self.ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
        self.ENABLE_ADMIN_SQL = _env_bool("ENABLE_ADMIN_SQL", False)
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
