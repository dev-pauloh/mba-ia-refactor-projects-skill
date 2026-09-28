from src.config.constants import API_VERSAO
from src.models import pedido_model, produto_model, usuario_model


def indice():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": API_VERSAO,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }


def status(ambiente):
    return {
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(),
            "usuarios": usuario_model.contar(),
            "pedidos": pedido_model.contar(),
        },
        "versao": API_VERSAO,
        "ambiente": ambiente,
    }
