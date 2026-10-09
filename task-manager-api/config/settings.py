"""Configuração da aplicação lida de variáveis de ambiente (.env opcional)."""
import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes')


def _env_list(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


def _secret(name):
    value = os.environ.get(name)
    if not value:
        logger.warning('%s não definida; usando valor aleatório (apenas desenvolvimento)', name)
        value = secrets.token_hex(32)
    return value


class Settings:
    SECRET_KEY = _secret('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _env_bool('FLASK_DEBUG', False)
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    CORS_ORIGINS = _env_list('CORS_ORIGINS')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    TOKEN_MAX_AGE = int(os.environ.get('TOKEN_MAX_AGE', '28800'))

    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
