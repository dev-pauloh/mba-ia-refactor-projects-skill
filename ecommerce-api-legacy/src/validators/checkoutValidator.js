const { CARD_NUMBER_PATTERN, EMAIL_PATTERN } = require('../config/constants');
const { ValidationError } = require('../errors');

function nonEmptyString(value) {
    return typeof value === 'string' && value.trim().length > 0;
}

function parsePositiveInteger(value) {
    if (typeof value === 'number' && Number.isInteger(value) && value > 0) return value;
    if (typeof value === 'string' && /^\d+$/.test(value) && Number(value) > 0) return Number(value);
    return null;
}

// Recebe o body com os nomes do contrato público (usr, eml, pwd, c_id, card).
function validateCheckout(body = {}) {
    const { usr, eml, pwd, c_id: rawCourseId, card } = body;
    const courseId = parsePositiveInteger(rawCourseId);
    const cardNumber = typeof card === 'string' ? card.replace(/[\s-]/g, '') : null;

    if (
        !nonEmptyString(usr)
        || !nonEmptyString(eml) || !EMAIL_PATTERN.test(eml.trim())
        || !nonEmptyString(pwd)
        || courseId === null
        || !cardNumber || !CARD_NUMBER_PATTERN.test(cardNumber)
    ) {
        throw new ValidationError('Bad Request');
    }

    return {
        name: usr.trim(),
        email: eml.trim().toLowerCase(),
        password: pwd,
        courseId,
        cardNumber,
    };
}

module.exports = { validateCheckout };
