import logging

from src.errors import ConflictError, NotFoundError
from src.models import produto_model
from src.services import produto_service

logger = logging.getLogger(__name__)


def listar():
    produtos = produto_model.listar()
    logger.info("Listando %d produtos", len(produtos))
    return produtos


def buscar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto


def pesquisar(termo, categoria, preco_min, preco_max):
    filtros = produto_service.validar_filtros_busca(termo, categoria, preco_min, preco_max)
    return produto_model.buscar(**filtros)


def criar(dados):
    produto = produto_service.validar_produto(dados)
    novo_id = produto_model.criar(**produto)
    logger.info("Produto criado id=%s", novo_id)
    return {"id": novo_id}


def atualizar(produto_id, dados):
    buscar(produto_id)
    produto = produto_service.validar_produto(dados)
    produto_model.atualizar(produto_id, **produto)


def deletar(produto_id):
    buscar(produto_id)
    if produto_model.possui_itens_pedido(produto_id):
        raise ConflictError("Produto possui pedidos e não pode ser excluído")
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
