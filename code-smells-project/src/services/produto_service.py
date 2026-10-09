"""Regras de domínio de produto — validação única usada por criação e atualização."""
from src.config.constants import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from src.errors import ValidationError
from src.services.validators import eh_inteiro, eh_numero, exigir_objeto, float_opcional, texto


def validar_produto(dados):
    exigir_objeto(dados)
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = texto(dados["nome"], "Nome deve ser texto")
    descricao = texto(dados.get("descricao", ""), "Descrição deve ser texto")
    categoria = texto(dados.get("categoria", CATEGORIA_PADRAO), "Categoria deve ser texto")
    preco = dados["preco"]
    estoque = dados["estoque"]

    if not eh_numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not eh_inteiro(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtros_busca(termo, categoria, preco_min, preco_max):
    return {
        "termo": termo or "",
        "categoria": categoria or None,
        "preco_min": float_opcional(preco_min, "preco_min deve ser numérico"),
        "preco_max": float_opcional(preco_max, "preco_max deve ser numérico"),
    }
