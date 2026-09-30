const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Simulação do gateway: cartões com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

module.exports = { PaymentStatus, APPROVED_CARD_PREFIX };
