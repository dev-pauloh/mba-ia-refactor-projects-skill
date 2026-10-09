from src.config.constants import API_VERSION
from src.models import health_model


def index():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": API_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }


def health():
    return {
        "status": "ok",
        "database": "connected",
        "counts": health_model.contagens(),
        "versao": API_VERSION,
    }
