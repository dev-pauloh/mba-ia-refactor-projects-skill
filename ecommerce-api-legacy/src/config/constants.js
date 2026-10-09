const DEFAULT_PORT = 3000;
const DEFAULT_DB_FILE = ':memory:';
const DEFAULT_LOG_LEVEL = 'info';

const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Gateway simulado: cartões iniciados por este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';
const CARD_NUMBER_PATTERN = /^\d{13,19}$/;
const CARD_VISIBLE_DIGITS = 4;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const PASSWORD_SALT_BYTES = 16;
const PASSWORD_KEY_LENGTH = 64;

const UNKNOWN_STUDENT = 'Unknown';

module.exports = {
    DEFAULT_PORT,
    DEFAULT_DB_FILE,
    DEFAULT_LOG_LEVEL,
    PAYMENT_STATUS,
    APPROVED_CARD_PREFIX,
    CARD_NUMBER_PATTERN,
    CARD_VISIBLE_DIGITS,
    EMAIL_PATTERN,
    PASSWORD_SALT_BYTES,
    PASSWORD_KEY_LENGTH,
    UNKNOWN_STUDENT,
};
