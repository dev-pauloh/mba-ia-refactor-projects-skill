const { PaymentStatus, APPROVED_CARD_PREFIX } = require('../config/constants');
const logger = require('../utils/logger');

// Gateway de pagamento simulado; a chave é injetada e nunca registrada em log.
class PaymentService {
    constructor({ gatewayKey }) {
        this.gatewayKey = gatewayKey;
    }

    charge(cardNumber, amount) {
        logger.info(`Processando pagamento de ${amount} no cartão final ${cardNumber.slice(-4)}`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
    }
}

module.exports = PaymentService;
