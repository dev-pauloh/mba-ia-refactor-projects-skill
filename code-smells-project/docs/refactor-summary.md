================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
code-smells-project/
├── app.py                         # lançador fino (python app.py)
├── requirements.txt
├── .env.example
├── README.md
├── docs/
│   ├── audit-report.md
│   └── refactor-summary.md
└── src/
    ├── __init__.py
    ├── app.py                     # composition root: create_app()
    ├── errors.py                  # AppError, ValidationError, UnauthorizedError, ForbiddenError, NotFoundError, ConflictError
    ├── config/
    │   ├── settings.py            # Settings via os.environ (SECRET_KEY, FLASK_DEBUG, HOST, PORT, DATABASE_PATH, CORS_ORIGINS, TOKEN_MAX_AGE, ENABLE_ADMIN_SQL)
    │   └── constants.py           # categorias, status, faixas de desconto, limites, versão
    ├── database/
    │   └── connection.py          # get_db() por requisição (flask.g), conexão read-only, init_db (schema+FK+UNIQUE, seed com hash, migração de senhas)
    ├── models/
    │   ├── produto_model.py
    │   ├── usuario_model.py
    │   ├── pedido_model.py        # listagem em 2 queries, criação transacional
    │   ├── relatorio_model.py     # agregados numa query
    │   ├── health_model.py
    │   └── admin_model.py         # reset transacional, SELECT em conexão somente leitura
    ├── services/
    │   ├── validators.py
    │   ├── produto_service.py     # validação única de produto e filtros de busca
    │   ├── usuario_service.py     # cadastro e credenciais
    │   ├── pedido_service.py      # itens, estoque, total, status
    │   ├── relatorio_service.py   # faixas de desconto
    │   ├── token_service.py       # token assinado itsdangerous
    │   └── notification_service.py
    ├── controllers/
    │   ├── produto_controller.py
    │   ├── usuario_controller.py
    │   ├── pedido_controller.py
    │   ├── relatorio_controller.py
    │   ├── health_controller.py
    │   └── admin_controller.py
    ├── views/                     # Blueprints finos (≤ 9 linhas por handler)
    │   ├── produto_routes.py
    │   ├── usuario_routes.py
    │   ├── pedido_routes.py
    │   ├── relatorio_routes.py
    │   ├── health_routes.py
    │   └── admin_routes.py
    └── middlewares/
        ├── auth.py                # require_auth / require_admin (Authorization: Bearer)
        └── error_handler.py       # handler central {"erro": ...}
```
Removidos (conteúdo 100% migrado): `controllers.py`, `models.py`, `database.py`.

## Findings addressed
| Finding | Sev. | Padrão | Rotas tratadas | Como o impacto foi verificado | Status |
|---|---|---|---|---|---|
| F01 SQL Injection | CRITICAL | PB-02, PB-13 | POST /login (exceção: emite credencial; só parametrização + validação), POST /usuarios (admin), POST /produtos (admin), PUT /produtos/<id> (admin), GET /produtos/busca (autenticado), POST /pedidos (dono ou admin) | `admin@loja.com' --` e `' OR '1'='1` no login → 401; `UNION SELECT ... FROM usuarios` na busca → 0 resultados; payload no nome gravado literal com tipo `cliente`; aspas em produto gravadas literalmente; PUT com `WHERE 1=1 --` altera 1 linha; `usuario_id`/`produto_id` injetados → 400; grep sem concatenação em `execute`; todas as rotas: 401 sem credencial e com token forjado, credencial válida = status do baseline | resolvido |
| F02 Admin/destrutivo/financeiro sem auth | CRITICAL | PB-13, PB-03 | POST /admin/reset-db, POST /admin/query, DELETE /produtos/<id>, GET /relatorios/vendas: Bearer admin | 401 sem credencial, 401 com token forjado, 403 para cliente, 200 para admin; `DELETE FROM produtos` e `SELECT 1; DELETE ...` via /admin/query → 400 e contagem inalterada; /admin/query → 403 com `ENABLE_ADMIN_SQL` no padrão; SQL movido para `admin_model` | resolvido |
| F03 Senha em texto puro | CRITICAL | PB-06 | POST /usuarios (admin), POST /login (exceção: emite credencial) | todas as senhas no banco começam com `scrypt:`; nenhuma senha do seed em claro; login de usuário novo valida hash; senha errada → 401; `loja.db` legado com texto puro migrado no boot e login `admin123` funciona | resolvido |
| F04 Exposição de senha e config | CRITICAL | PB-06, PB-13 | GET /usuarios (admin), GET /usuarios/<id> (dono ou admin), GET /health (autenticado) | respostas sem `senha`; health sem `secret_key/db_path/debug/ambiente`; cliente lendo outro usuário → 403; 401 sem credencial/token forjado | resolvido |
| F05 SECRET_KEY hardcoded | CRITICAL | PB-01, PB-06, PB-13 | GET /health (autenticado) | grep `minha-chave` e de segredos literais = 0; token assinado com a chave antiga → 401 em todas as rotas protegidas; warning de chave aleatória quando `SECRET_KEY` está ausente; `.env.example` criado | resolvido |
| F06 Arquivos-deus | CRITICAL | PB-03 | nenhuma | `app.py` virou lançador de 14 linhas; `execute(` só em `src/models` e `src/database`; views e controllers não importam `database`; um arquivo por entidade em cada camada | resolvido |
| F07 Autenticação inexistente | HIGH | PB-13 | admin: POST /produtos, PUT /produtos/<id>, GET /usuarios, GET /pedidos, PUT /pedidos/<id>/status; dono ou admin: GET /usuarios/<id>, GET /pedidos/usuario/<id>, POST /pedidos | matriz: 401 sem credencial e com token forjado, 403 para cliente nas rotas admin, status do baseline com credencial; cliente criando pedido para outro usuário → 403; listando pedidos de outro → 403; próprios pedidos → 200; token lixo → 401 | resolvido |
| F08 Config insegura | HIGH | PB-01 | todas (CORS/debug) | log `Debug mode: off`; `app.debug == False`; exceção forçada → 500 JSON genérico, sem debugger; HOST padrão 127.0.0.1; sem `Access-Control-Allow-Origin` para origem arbitrária; com `CORS_ORIGINS=http://loja.local` só essa origem recebe o header | resolvido |
| F09 Conexão global | HIGH | PB-05 | todas exceto GET / | grep `global`/`check_same_thread` = 0; 60 requisições paralelas (20 pedidos + 40 leituras): 0 erros, estoque 50 → 30 e 20 itens, consistente | resolvido |
| F10 Acoplamento ao banco | HIGH | PB-05 | nenhuma | conexão obtida só via `src/database/connection.get_db()` (o `get_connection()` da recomendação); `from src.database` só em models e no composition root; SQL de health/admin em `health_model`/`admin_model` | resolvido |
| F11 Regra na camada HTTP/dados | HIGH | PB-04 | nenhuma | regras em `produto_service`, `pedido_service`, `relatorio_service`; notificações em `notification_service`; views só leem o request e chamam um controller; o único `raise` restante em model é o débito condicional de estoque, que precisa ficar na transação (F13) | resolvido |
| F12 N+1 | MEDIUM | PB-07 | GET /pedidos, GET /pedidos/usuario/<id>, GET /relatorios/vendas | SELECTs contados por trace do SQLite: (2, 2, 1) com 1, 5 e 20 pedidos (antes: 1 + P + P·I e 5) | resolvido |
| F13 Sem transação/integridade | MEDIUM | PB-10 | POST /pedidos, DELETE /produtos/<id>, POST /admin/reset-db | pedido que estoura estoque no 2º item → 400, estoque e nº de pedidos inalterados, 0 itens órfãos; DELETE de produto com pedidos → 409 e produto preservado; reset em `with conn:`; FK + `PRAGMA foreign_keys=ON` | resolvido |
| F14 Validação/mapeamento duplicados | MEDIUM | PB-12 | PUT /produtos/<id> | PUT com nome de 1 caractere → 400; com categoria inexistente → 400; um único `validar_produto`, `produto_to_dict`, `usuario_to_dict` (login deriva dele) e `pedido_model.listar(usuario_id=None)` | resolvido |
| F15 Validação fraca | MEDIUM | PB-12 | POST /produtos, PUT /produtos/<id>, GET /produtos/busca, POST /usuarios, POST /login, POST /pedidos, PUT /pedidos/<id>/status | preço/estoque string → 400; `preco_min=abc` → 400; login sem body → 400; e-mail inválido → 400; e-mail duplicado → 409 (+ índice UNIQUE); quantidade -5 → 400 e estoque inalterado; itens não-lista → 400; status sem body → 400; pedido inexistente → 404 | resolvido |
| F16 Erros vazando detalhes | MEDIUM | PB-09 | as 17 rotas listadas no finding | grep `except Exception`/`str(e)` = 0; erro de SQL → 400 genérico sem "no such table"; exceção inesperada → 500 `{"erro": "Erro interno do servidor"}` com stack trace só no log; 404/405 em JSON `{"erro": ...}` | resolvido |
| F17 Magic numbers | LOW | PB-12 | nenhuma | literais de regra só em `src/config/constants.py`; porta via `PORT` | resolvido |
| F18 Nomenclatura | LOW | PB-12 | nenhuma | grep `cursor2/cursor3`, `prod`, parâmetros `id` = 0 | resolvido |
| F19 Imports não usados | LOW | PB-14 | nenhuma | checagem AST de imports não usados = 0 | resolvido |
| F20 print como logging | LOW | PB-14 | nenhuma | grep `\bprint(` = 0; `logging` configurado no lançador; notificações via `notification_service`; logs de login e cadastro registram só o id, nunca o e-mail | resolvido |

Rotas públicas mantidas (mvc-guidelines §6, regra 5): `GET /`, `GET /produtos`, `GET /produtos/<id>`. Elas não aparecem em nenhum finding coberto pela regra 2 (CRITICAL ou de autenticação/exposição). Aparecem só no `Routes:` de F08 (CORS/debug) e F16 (detalhes de erro), cujos impactos não dependem de identidade: foram eliminados por config e pelo error handler e verificados acima. Por isso não há recomendação residual de autenticação pendente para elas.

## Intentional contract changes
- **POST /login**: exceção da regra 2 (emite a credencial) e continua pública. A resposta ganhou a chave `token` (Bearer assinado com `SECRET_KEY`, expira em `TOKEN_MAX_AGE`). Entrada inválida passou a dar 400.
- **Autenticação nova (sem credencial → 401, sem permissão → 403):**
  - **admin**: POST /produtos, PUT /produtos/<id>, DELETE /produtos/<id>, GET /usuarios, POST /usuarios, GET /pedidos, PUT /pedidos/<id>/status, GET /relatorios/vendas, POST /admin/reset-db, POST /admin/query
  - **dono ou admin**: GET /usuarios/<id>, GET /pedidos/usuario/<id>, POST /pedidos (`usuario_id` precisa ser o do token)
  - **autenticado**: GET /produtos/busca, GET /health
- **POST /admin/query**: desabilitada por padrão (`ENABLE_ADMIN_SQL=false` → 403). Habilitada, aceita uma única instrução SELECT numa conexão somente leitura; qualquer outra instrução → 400, e não existe mais a resposta `{"mensagem": "Query executada"}`.
- **GET /health**: removidas as chaves `secret_key`, `db_path`, `debug` e `ambiente`.
- **GET /usuarios, GET /usuarios/<id>**: removido o campo `senha` de cada usuário.
- **DELETE /produtos/<id>**: produto com itens de pedido → 409, para preservar o histórico.
- **PUT /pedidos/<id>/status**: pedido inexistente → 404 (antes, 200).
- **POST /usuarios**: e-mail duplicado → 409; e-mail com formato inválido → 400.
- **Entradas inválidas** que antes davam 500 (tipos errados, body ausente, `preco_min` não numérico) agora dão 400. PUT /produtos/<id> aplica as mesmas regras de nome e categoria do POST.
- **Erros**: envelope `{"erro": ..., "sucesso": false}` em todas as respostas de erro; 500 com mensagem genérica.
- **Operacional**: `HOST` padrão `127.0.0.1` (antes `0.0.0.0`), debug desligado por padrão, CORS só para as origens de `CORS_ORIGINS`.

## Validation
  ✓ Application boots without errors (`python app.py`)
  ✓ All endpoints respond correctly (19/19 match baseline)
  ✓ Every finding's impact no longer reproduces (20/20 findings)
  ✓ Every route cited in auth/exposure findings or CRITICAL findings requires credentials (15/15, except the login route)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining

| Método | Path | Status antes | Status depois |
|---|---|---|---|
| GET | / | 200 | 200 |
| POST | /login | 200 | 200 |
| GET | /health | 200 | 200 (Bearer) |
| GET | /produtos | 200 | 200 |
| GET | /produtos/busca | 200 | 200 (Bearer) |
| GET | /produtos/<id> | 200 | 200 |
| GET | /usuarios | 200 | 200 (Bearer admin) |
| GET | /usuarios/<id> | 200 | 200 (Bearer dono/admin) |
| POST | /usuarios | 201 | 201 (Bearer admin) |
| POST | /produtos | 201 | 201 (Bearer admin) |
| PUT | /produtos/<id> | 200 | 200 (Bearer admin) |
| POST | /pedidos | 201 | 201 (Bearer dono/admin) |
| GET | /pedidos | 200 | 200 (Bearer admin) |
| GET | /pedidos/usuario/<usuario_id> | 200 | 200 (Bearer dono/admin) |
| GET | /relatorios/vendas | 200 | 200 (Bearer admin) |
| PUT | /pedidos/<pedido_id>/status | 200 | 200 (Bearer admin) |
| POST | /admin/query | 200 | 200 (Bearer admin + ENABLE_ADMIN_SQL=true) |
| DELETE | /produtos/<id> | 200 | 200 (Bearer admin) |
| POST | /admin/reset-db | 200 | 200 (Bearer admin) |

Matriz de credenciais (rotas protegidas): sem credencial → 401 (15/15); token forjado com a SECRET_KEY antiga → 401 (15/15); cliente em rota admin → 403 (10/10); credencial válida → status do baseline (15/15). Ao todo, 100/100 checagens de impacto passaram.
================================
