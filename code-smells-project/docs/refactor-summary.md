```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── app.py                          # lançador fino (python app.py)
├── requirements.txt
├── .env.example
├── README.md
├── docs/
│   ├── audit-report.md
│   └── refactor-summary.md
└── src/
    ├── __init__.py
    ├── app.py                      # composition root: create_app()
    ├── errors.py                   # AppError, ValidationError, UnauthorizedError, ForbiddenError, NotFoundError
    ├── config/
    │   ├── settings.py             # Settings lidas do ambiente
    │   └── constants.py            # categorias, status, limites, faixas de desconto
    ├── database/
    │   └── connection.py           # get_db() por app context, schema, seed com hash
    ├── models/
    │   ├── produto_model.py
    │   ├── usuario_model.py
    │   ├── pedido_model.py
    │   ├── relatorio_model.py
    │   └── admin_model.py
    ├── controllers/
    │   ├── produto_controller.py
    │   ├── usuario_controller.py
    │   ├── pedido_controller.py
    │   ├── relatorio_controller.py
    │   ├── health_controller.py
    │   └── admin_controller.py
    ├── services/
    │   └── notification_service.py
    ├── views/
    │   ├── produto_routes.py
    │   ├── usuario_routes.py
    │   ├── pedido_routes.py
    │   ├── relatorio_routes.py
    │   ├── health_routes.py
    │   └── admin_routes.py
    └── middlewares/
        ├── error_handler.py
        └── auth.py

## Findings addressed
| Finding | Severidade | Padrão | Status |
|---|---|---|---|
| F01 SQL Injection | CRITICAL | PB-02 | Resolvido: todas as queries com placeholders `?`; busca dinâmica com lista de cláusulas + parâmetros |
| F02 Admin SQL/reset sem auth | CRITICAL | PB-13 | Resolvido: `@require_admin` (X-Admin-Token, hmac.compare_digest); /admin/query desabilitado por padrão (ENABLE_ADMIN_SQL) |
| F03 Secret hardcoded/exposta | CRITICAL | PB-01, PB-06 | Resolvido: SECRET_KEY do ambiente (aleatória se ausente); removida do /health |
| F04 Senha em texto puro | CRITICAL | PB-06 | Resolvido: generate/check_password_hash (werkzeug) no cadastro, login e seed |
| F05 Senha na resposta | CRITICAL | PB-06 | Resolvido: serialização pública sem `senha` |
| F06 God File | CRITICAL | PB-03 | Resolvido: models/controllers/views/services por entidade; controllers.py, models.py e database.py removidos |
| F07 Regra na camada HTTP/dados | HIGH | PB-04 | Resolvido: regras nos controllers, notificações em notification_service; cancelamento agora devolve estoque |
| F08 Conexão global mutável | HIGH | PB-05 | Resolvido: conexão por requisição em flask.g, fechada no teardown |
| F09 Config insegura | HIGH | PB-01 | Resolvido: DEBUG=false, HOST=127.0.0.1, CORS só com CORS_ORIGINS, APP_ENV do ambiente |
| F10 Autenticação ausente | HIGH | PB-13 | Parcial: rotas admin e relatório financeiro protegidas; login continua sem emitir token e CRUD continua público (mvc-guidelines §6.5) — ver recomendação residual |
| F11 Acoplamento sem DI | HIGH | PB-05 | Resolvido: get_db() (fábrica por requisição) só em models/database; controllers dependem de models/services |
| F12 N+1 | MEDIUM | PB-07 | Resolvido: pedidos + itens em 2 queries (LEFT JOIN + IN); relatório com GROUP BY status |
| F13 Sem transação | MEDIUM | PB-10 | Resolvido: `with db:` em todas as escritas; baixa de estoque atômica (`estoque >= ?`). Delete de produto mantém itens históricos (exibidos como "Desconhecido", igual ao original) |
| F14 Erro espalhado/vazando | MEDIUM | PB-09 | Resolvido: error handler central; 500 com mensagem genérica e stack trace só no log |
| F15 Validação duplicada/fraca | MEDIUM | PB-12 | Resolvido: validar_produto único para create/update, tipos checados, itens de pedido validados |
| F16 Mapeamento duplicado | MEDIUM | PB-12 | Resolvido: um `_to_dict` por entidade; query de pedidos compartilhada |
| F17 print como logging | LOW | PB-14 | Resolvido: módulo logging configurado no create_app |
| F18 Magic numbers | LOW | PB-12 | Resolvido: src/config/constants.py |
| F19 Imports não usados | LOW | PB-14 | Resolvido: arquivos originais removidos, sem imports mortos |
| F20 Nomenclatura | LOW | PB-12 | Resolvido: produto_id/usuario_id/pedido_id, sem cursor2/cursor3 |
| F21 SQL no health | LOW | PB-04 | Resolvido: contagens via `<model>.contar()` |

## Intentional contract changes
- GET /usuarios e GET /usuarios/<id>: campo `senha` removido de `dados` (segurança).
- GET /health: removidos `secret_key`, `db_path`, `debug`; `ambiente` vem de APP_ENV (padrão "development").
- POST /admin/reset-db, POST /admin/query, GET /relatorios/vendas: exigem header `X-Admin-Token` = ADMIN_TOKEN (sem token → 401; ADMIN_TOKEN vazio → sempre 401).
- POST /admin/query: além do token, retorna 403 se ENABLE_ADMIN_SQL não for `true`.
- Entradas inválidas que davam 500 agora dão 400 (preço/estoque não numéricos, preco_min/preco_max inválidos, body ausente em /login e /pedidos/<id>/status, itens com quantidade <= 0).
- PUT /produtos/<id> passa a aplicar a mesma validação do POST (nome 2-200 caracteres, categoria válida).
- PUT /pedidos/<id>/status: pedido inexistente → 404 (antes 200 sem efeito); mudar para "cancelado" devolve o estoque dos itens.
- Erros 500 retornam `{"erro": "Erro interno do servidor"}` em vez da mensagem da exceção; rotas inexistentes retornam JSON `{"erro": ...}` 404.
- Servidor: padrão HOST=127.0.0.1 (antes 0.0.0.0), debug desligado, CORS desligado a menos que CORS_ORIGINS seja definido.
- Bancos `loja.db` antigos (senhas em texto puro) são incompatíveis com o login: apague o arquivo para o seed recriar com hash.

Recomendações residuais: emitir token assinado no /login (itsdangerous) e proteger GET /usuarios, GET /pedidos e DELETE /produtos quando os clientes puderem enviar credenciais; validar existência de usuario_id em POST /pedidos.

## Validation
  ✓ Application boots without errors (`python app.py`)
  ✓ All endpoints respond correctly (27/27 match baseline status; key diffs only the intentional removals above)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (F10 parcial por decisão de contrato; ver acima)
| Método | Path | Status antes | Status depois |
|---|---|---|---|
| GET | / | 200 | 200 |
| GET | /health | 200 | 200 |
| GET | /produtos | 200 | 200 |
| GET | /produtos/busca?q=Mouse&categoria=informatica&preco_min=10&preco_max=500 | 200 | 200 |
| GET | /produtos/1 | 200 | 200 |
| GET | /produtos/999 | 404 | 404 |
| POST | /produtos (válido) | 201 | 201 |
| POST | /produtos (inválido) | 400 | 400 |
| PUT | /produtos/11 | 200 | 200 |
| GET | /usuarios | 200 | 200 |
| GET | /usuarios/1 | 200 | 200 |
| GET | /usuarios/999 | 404 | 404 |
| POST | /usuarios | 201 | 201 |
| POST | /login (admin) | 200 | 200 |
| POST | /login (usuário novo) | 200 | 200 |
| POST | /login (senha errada) | 401 | 401 |
| POST | /pedidos (válido) | 201 | 201 |
| POST | /pedidos (sem estoque) | 400 | 400 |
| GET | /pedidos | 200 | 200 |
| GET | /pedidos/usuario/2 | 200 | 200 |
| PUT | /pedidos/1/status (aprovado) | 200 | 200 |
| PUT | /pedidos/1/status (inválido) | 400 | 400 |
| GET | /relatorios/vendas (com X-Admin-Token) | 200 | 200 |
| DELETE | /produtos/11 | 200 | 200 |
| DELETE | /produtos/11 (de novo) | 404 | 404 |
| POST | /admin/query (token + ENABLE_ADMIN_SQL=true) | 200 | 200 |
| POST | /admin/reset-db (com X-Admin-Token) | 200 | 200 |
================================
```
