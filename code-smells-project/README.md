# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para MVC
(ver `docs/audit-report.md` e `docs/refactor-summary.md`).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: exporte as variáveis no shell
export SECRET_KEY=um-valor-aleatorio-longo
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (`HOST`/`PORT` configuráveis). O banco SQLite (`loja.db`, ou `DATABASE_PATH`)
é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas como hash).
Bancos antigos com senhas em texto puro são migrados para hash no boot.

## Autenticação

`POST /login` devolve um `token` assinado (validade `TOKEN_MAX_AGE`, padrão 1h). Envie-o nas rotas protegidas:

```
Authorization: Bearer <token>
```

| Acesso | Rotas |
|---|---|
| Público | `GET /`, `GET /produtos`, `GET /produtos/<id>`, `POST /login` |
| Autenticado | `GET /produtos/busca`, `GET /health` |
| Próprio usuário ou admin | `GET /usuarios/<id>`, `GET /pedidos/usuario/<id>`, `POST /pedidos` |
| Admin | `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`, `GET /usuarios`, `POST /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`, `POST /admin/reset-db`, `POST /admin/query` |

`POST /admin/query` só aceita uma instrução `SELECT`, roda em conexão somente leitura e fica desabilitada
até `ENABLE_ADMIN_SQL=true`.

Usuários de exemplo: `admin@loja.com` / `admin123` (admin), `joao@email.com` / `123456` (cliente).

## Estrutura

```
app.py              # lançador (python app.py)
src/app.py          # composition root: create_app()
src/config/         # settings (variáveis de ambiente) e constantes de domínio
src/database/       # conexão por requisição, schema, seed
src/models/         # acesso a dados (SQL parametrizado)
src/services/       # regras de domínio, tokens e notificações
src/controllers/    # casos de uso
src/views/          # Blueprints (HTTP)
src/middlewares/    # autenticação e error handler central
```
