import logging

from src.config.constants import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from src.errors import NotFoundError, ValidationError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _is_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_produto(dados):
    """Validação única usada por criação e atualização."""
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not _is_numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser um número inteiro")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def _parse_preco(valor, campo):
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{campo} deve ser numérico")


def listar():
    produtos = produto_model.listar()
    logger.info("Listando %s produtos", len(produtos))
    return produtos


def buscar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado", com_sucesso=True)
    return produto


def pesquisar(termo, categoria, preco_min, preco_max):
    return produto_model.buscar(
        termo,
        categoria,
        _parse_preco(preco_min, "preco_min"),
        _parse_preco(preco_max, "preco_max"),
    )


def criar(dados):
    produto = validar_produto(dados)
    produto_id = produto_model.criar(**produto)
    logger.info("Produto criado id=%s", produto_id)
    return {"id": produto_id}


def atualizar(produto_id, dados):
    if not produto_model.buscar_por_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    produto = validar_produto(dados)
    produto_model.atualizar(produto_id, **produto)


def deletar(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
