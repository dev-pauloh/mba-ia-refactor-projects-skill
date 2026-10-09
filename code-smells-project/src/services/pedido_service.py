"""Regras de domínio de pedido: validação dos itens, estoque e total."""
from src.config.constants import STATUS_PEDIDO
from src.errors import ValidationError
from src.services.validators import exigir_objeto, inteiro_positivo


def validar_pedido(dados):
    exigir_objeto(dados)
    if not dados.get("usuario_id"):
        raise ValidationError("Usuario ID é obrigatório")
    usuario_id = inteiro_positivo(dados["usuario_id"], "Usuario ID inválido")

    itens = dados.get("itens", [])
    if not isinstance(itens, list) or not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    validados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item de pedido inválido")
        validados.append({
            "produto_id": inteiro_positivo(item.get("produto_id"), "produto_id deve ser um inteiro positivo"),
            "quantidade": inteiro_positivo(item.get("quantidade"), "quantidade deve ser um inteiro positivo"),
        })
    return usuario_id, validados


def precificar_itens(itens, produtos):
    """Confere existência e estoque e devolve (itens com preço, total).

    `produtos` é um dict {produto_id: produto}.
    """
    precificados = []
    total = 0
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError("Estoque insuficiente para " + produto["nome"])
        total += produto["preco"] * item["quantidade"]
        precificados.append({**item, "nome": produto["nome"], "preco_unitario": produto["preco"]})
    return precificados, total


def validar_status(dados):
    status = dados.get("status", "") if isinstance(dados, dict) else ""
    if status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    return status
