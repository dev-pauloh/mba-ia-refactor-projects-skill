const crypto = require('crypto');
const logger = require('../utils/logger');

function secret(name) {
    if (process.env[name]) return process.env[name];
    logger.warn(`${name} não definida; usando valor aleatório (apenas desenvolvimento)`);
    return crypto.randomBytes(32).toString('hex');
}

module.exports = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    dbFile: process.env.DB_FILE || ':memory:',
    paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
    adminToken: process.env.ADMIN_TOKEN || '',
    seedUserPassword: process.env.SEED_USER_PASSWORD || crypto.randomBytes(12).toString('hex'),
});
