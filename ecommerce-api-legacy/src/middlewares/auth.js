const crypto = require('crypto');
const { UnauthorizedError } = require('../errors');

module.exports = ({ adminToken }) => (req, res, next) => {
    const provided = Buffer.from(req.get('X-Admin-Token') || '');
    const expected = Buffer.from(adminToken || '');
    if (!expected.length || provided.length !== expected.length || !crypto.timingSafeEqual(provided, expected)) {
        return next(new UnauthorizedError('Não autorizado'));
    }
    return next();
};
