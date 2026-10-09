const crypto = require('crypto');
const { promisify } = require('util');
const { PASSWORD_SALT_BYTES, PASSWORD_KEY_LENGTH } = require('../config/constants');

const scrypt = promisify(crypto.scrypt);

async function hashPassword(password) {
    const salt = crypto.randomBytes(PASSWORD_SALT_BYTES).toString('hex');
    const hash = await scrypt(password, salt, PASSWORD_KEY_LENGTH);
    return `${salt}:${hash.toString('hex')}`;
}

async function verifyPassword(password, stored) {
    const [salt, hash] = String(stored || '').split(':');
    if (!salt || !hash) return false;
    const expected = Buffer.from(hash, 'hex');
    if (expected.length !== PASSWORD_KEY_LENGTH) return false;
    const candidate = await scrypt(password, salt, PASSWORD_KEY_LENGTH);
    return crypto.timingSafeEqual(candidate, expected);
}

module.exports = { hashPassword, verifyPassword };
