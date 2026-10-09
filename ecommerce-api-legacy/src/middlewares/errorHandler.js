const { AppError } = require('../errors');

const BAD_REQUEST = 400;
const SERVER_ERROR = 500;

function createErrorHandler({ logger }) {
    return (err, req, res, next) => {
        if (err instanceof AppError) {
            return res.status(err.statusCode).send(err.message);
        }
        // Erros do body parser do Express (JSON malformado, payload grande) carregam status 4xx.
        if (err.status >= BAD_REQUEST && err.status < SERVER_ERROR) {
            return res.status(BAD_REQUEST).send('Bad Request');
        }
        logger.error(`Erro não tratado em ${req.method} ${req.path}`, err);
        return res.status(SERVER_ERROR).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
