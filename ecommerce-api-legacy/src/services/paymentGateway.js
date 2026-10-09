const { PAYMENT_STATUS, APPROVED_CARD_PREFIX, CARD_VISIBLE_DIGITS } = require('../config/constants');

// Gateway simulado; a chave fica encapsulada aqui e nunca é registrada em log.
class PaymentGateway {
    #apiKey;

    constructor({ apiKey, logger }) {
        this.#apiKey = apiKey;
        this.logger = logger;
    }

    async charge({ cardNumber, amount }) {
        const status = cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        this.logger.info(`Pagamento ${status} cartão final ${cardNumber.slice(-CARD_VISIBLE_DIGITS)} valor ${amount}`);
        return status;
    }
}

module.exports = { PaymentGateway };
