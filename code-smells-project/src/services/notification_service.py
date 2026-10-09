"""Efeitos colaterais de notificação. Hoje só registram em log; é o ponto de troca
para integrações reais (e-mail, SMS, push)."""
import logging

from src.config.constants import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação [email]: pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("Notificação [sms]: pedido %s recebido", pedido_id)
    logger.info("Notificação [push]: novo pedido %s recebido pelo sistema", pedido_id)


def status_pedido_alterado(pedido_id, novo_status):
    if novo_status == STATUS_APROVADO:
        logger.info("Notificação: pedido %s aprovado; preparar envio", pedido_id)
    elif novo_status == STATUS_CANCELADO:
        logger.info("Notificação: pedido %s cancelado; devolver estoque", pedido_id)
