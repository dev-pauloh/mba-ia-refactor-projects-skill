const crypto = require('crypto');
const { DEFAULT_PORT, DEFAULT_DB_FILE, DEFAULT_LOG_LEVEL } = require('./constants');

// Carrega .env opcional (stdlib do Node >= 20.12); variáveis já definidas no ambiente prevalecem.
try {
    process.loadEnvFile();
} catch (err) {
    if (err.code !== 'ENOENT') throw err;
}

const warnings = [];

function secret(name) {
    if (process.env[name]) return process.env[name];
    warnings.push(`${name} não definida; usando valor aleatório (apenas desenvolvimento)`);
    return crypto.randomBytes(32).toString('hex');
}

const config = Object.freeze({
    port: Number(process.env.PORT) || DEFAULT_PORT,
    dbFile: process.env.DB_FILE || DEFAULT_DB_FILE,
    logLevel: process.env.LOG_LEVEL || DEFAULT_LOG_LEVEL,
    paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
    // Sem valor, as rotas administrativas ficam bloqueadas (falha fechada).
    adminApiToken: process.env.ADMIN_API_TOKEN || '',
    warnings: Object.freeze(warnings),
});

module.exports = config;
