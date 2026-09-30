const { AppError } = require('../errors');
const logger = require('../utils/logger');

// Mantém o formato original de erro da API: texto simples.
module.exports = (err, req, res, next) => {
    if (res.headersSent) return next(err);
    if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
    if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
    logger.error(`Erro não tratado em ${req.method} ${req.originalUrl}`, err);
    return res.status(500).send('Erro interno');
};
