import logging

from src.config.constants import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    # Ponto de integração com provedores reais de e-mail/SMS/push.
    logger.info("Notificação email: pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("Notificação sms: pedido %s recebido", pedido_id)
    logger.info("Notificação push: novo pedido %s recebido pelo sistema", pedido_id)


def pedido_status_alterado(pedido_id, novo_status):
    if novo_status == STATUS_APROVADO:
        logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)
    elif novo_status == STATUS_CANCELADO:
        logger.info("Notificação: pedido %s cancelado, estoque devolvido", pedido_id)
