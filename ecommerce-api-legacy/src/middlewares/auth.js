const crypto = require('crypto');
const { UnauthorizedError } = require('../errors');

const BEARER_PREFIX = 'Bearer ';

function digest(value) {
    return crypto.createHash('sha256').update(value).digest();
}

// Exige `Authorization: Bearer <ADMIN_API_TOKEN>`; sem token configurado, nega tudo (falha fechada).
function createRequireAdmin({ adminApiToken }) {
    const expected = adminApiToken ? digest(adminApiToken) : null;

    return (req, res, next) => {
        const header = req.get('Authorization') || '';
        const provided = header.startsWith(BEARER_PREFIX) ? header.slice(BEARER_PREFIX.length) : '';
        if (!expected || !provided || !crypto.timingSafeEqual(digest(provided), expected)) {
            return next(new UnauthorizedError());
        }
        return next();
    };
}

module.exports = { createRequireAdmin };
