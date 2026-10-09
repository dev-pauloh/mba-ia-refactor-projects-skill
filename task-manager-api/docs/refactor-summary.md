```
================================
PHASE 3: REFACTORING COMPLETE
================================
```

## New Project Structure

```
task-manager-api/
├── app.py                        # composition root: create_app() + lançador (`python app.py`)
├── database.py                   # db (Flask-SQLAlchemy) + init_db() com PRAGMA foreign_keys=ON
├── seed.py                       # popula o banco (senhas com hash werkzeug, ≥ 8 caracteres)
├── requirements.txt              # flask, flask-sqlalchemy, flask-cors, python-dotenv
├── .env.example
├── README.md
├── config/
│   ├── settings.py               # Settings lidas do ambiente/.env (SECRET_KEY, DATABASE_URL, DEBUG, HOST, PORT, CORS, SMTP...)
│   └── constants.py              # status, roles, limites, prioridades, cor padrão, janela de atividade
├── models/                       # Model: entidades + regras intrínsecas (is_overdue, hash de senha)
│   ├── task.py
│   ├── user.py
│   └── category.py
├── services/                     # regras de domínio + acesso ao ORM; integrações
│   ├── task_service.py
│   ├── user_service.py
│   ├── category_service.py
│   ├── report_service.py
│   ├── token_service.py          # token assinado com expiração (itsdangerous)
│   └── notification_service.py   # SMTP injetado, sem estado em memória
├── controllers/                  # validação da entrada + orquestração + formato da resposta
│   ├── validation.py
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── routes/                       # View: Blueprints finos (URL → controller → jsonify)
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py
│   ├── report_routes.py
│   └── system_routes.py          # GET /, GET /health
├── middlewares/
│   ├── auth.py                   # login_required, roles_required, self_or_roles
│   └── error_handler.py          # handlers JSON centrais (400/401/403/404/405/409/500) + rollback + log
├── utils/
│   ├── errors.py                 # ValidationError, UnauthorizedError, ForbiddenError, NotFoundError, ConflictError
│   └── helpers.py                # utcnow(), calculate_percentage()
└── docs/
    ├── audit-report.md
    └── refactor-summary.md
```

## Findings addressed

| Finding | Sev. | Padrão | Rotas tratadas | Como o impacto foi verificado | Status |
|---|---|---|---|---|---|
| F01 Endpoints sem auth/autorização | CRITICAL | PB-13 | Token Bearer em todas as 19: GET/POST /tasks, GET/PUT/DELETE /tasks/<id>, GET /tasks/search, GET /tasks/stats, GET /categories (autenticado); GET /users, GET /reports/summary, POST/PUT/DELETE /categories (admin/manager); POST /users, DELETE /users/<id> (admin); GET /users/<id>, GET /users/<id>/tasks, GET /reports/user/<id> (próprio ou admin/manager); PUT /users/<id> (próprio ou admin; role/active só admin) | 19/19 rotas → 401 sem token e status do baseline com token de admin; 29 checagens de papel: user comum recebe 403 ao listar usuários, criar admin, promover/desativar a si mesmo, apagar usuário, ver relatório global ou de outro usuário, alterar categorias; manager recebe 403 em POST /users, PUT /users/1, DELETE /users/1 | resolvido |
| F02 Hash de senha nas respostas | CRITICAL | PB-06, PB-13 | GET /users/<id>, POST /users, PUT /users/<id> (auth conforme F01); POST /login (exceção: emite credencial) | `password` ausente do JSON das 4 rotas (incluindo `user` do login); grep `'password': self` sem ocorrências | resolvido |
| F03 MD5 sem salt + senha de 4 caracteres | CRITICAL | PB-06 | POST /users, PUT /users/<id> (auth conforme F01); POST /login (exceção: emite credencial) | hashes no banco = `scrypt:32768:8:1`; POST/PUT /users com senha < 8 → 400; seed não tem mais senhas de 4 caracteres (login `joao/1234` → 401); grep `hashlib` sem ocorrências | resolvido |
| F04 Segredos/config hardcoded | CRITICAL | PB-01 | nenhuma | grep do sinal AP-01 sem ocorrências; SECRET_KEY, DATABASE_URL e SMTP_* vêm de config/settings.py (dotenv); SECRET_KEY aleatória + warning quando ausente; `.env.example` criado | resolvido |
| F05 Token falso | HIGH | PB-13 | POST /login (exceção: emite credencial) | `fake-jwt-token-1` e token adulterado → 401 (inclusive em DELETE /users/1); token expirado e token de outra chave rejeitados (teste em processo); usuário inativo → 403 no login | resolvido |
| F06 Debug, bind 0.0.0.0, CORS aberto | HIGH | PB-01 | POST /tasks, PUT /tasks/<id>, GET /tasks/search, POST /users, PUT /users/<id>, PUT /categories/<id>; CORS em todas | log `Debug mode: off`; as entradas que antes abriam o debugger (HTML 500 com `__debugger__`) agora retornam 400 JSON; `Origin: http://evil.example` não recebe `Access-Control-Allow-Origin`; HOST padrão 127.0.0.1 | resolvido |
| F07 Regra/ORM nas rotas | HIGH | PB-04 | nenhuma | grep de `db.`/`select(`/loops/`round(` em routes/ sem ocorrências; handlers com 1 linha; CRUD de categorias movido para category_routes/controller/service | resolvido |
| F08 Validação ausente | MEDIUM | PB-12 | POST /tasks, PUT /tasks/<id>, GET /tasks/search, POST /users, PUT /users/<id>, POST /categories, PUT /categories/<id> | 14 entradas inválidas (priority string, title numérico, tags int, user_id não numérico, email/senha não-string, name vazio, active não booleano, color inválida, body null) → 400 JSON com mensagem | resolvido |
| F09 Erros engolidos, sem handler central | MEDIUM | PB-09 | GET /tasks, POST /tasks, PUT /tasks/<id>, DELETE /tasks/<id>, POST /users, PUT /users/<id>, DELETE /users/<id>, POST /categories, PUT /categories/<id>, DELETE /categories/<id> | grep `except:`/`except Exception` sem ocorrências; 404 e 405 em JSON; erro inesperado → `logger.exception` + 500 JSON + rollback | resolvido |
| F10 Categoria excluída deixa tasks órfãs | MEDIUM | PB-10 | DELETE /categories/<id> | task criada na categoria fica com `category_id: null` após o DELETE (UPDATE + DELETE no mesmo commit); DDL de `tasks` contém `ON DELETE SET NULL` e `ON DELETE CASCADE`; PRAGMA foreign_keys ativo. Obs.: no baseline o backref do ORM já anulava o FK implicitamente, então o impacto era latente (sem garantia no banco) | resolvido |
| F11 N+1 | MEDIUM | PB-07 | GET /tasks, GET /users, GET /reports/summary, GET /categories, GET /tasks/stats | contagem de queries por requisição constante após inserir +20 tasks, +5 usuários e +5 categorias (2, 2, 10, 2, 4) | resolvido |
| F12 Lógica duplicada | MEDIUM | PB-12 | nenhuma | grep da condição de atraso inline sem ocorrências; Task.is_overdue e to_dict reutilizados; validadores únicos para create/update; constantes em config/constants.py | resolvido |
| F13 NotificationService acoplado | MEDIUM | PB-05 | nenhuma | teste com SMTP fake injetado envia sem servidor real; atributo `notifications` removido; sem SMTP configurado apenas loga | resolvido |
| F14 APIs deprecated | MEDIUM | PB-11 | nenhuma | grep `datetime.utcnow`/`.query.` sem ocorrências; app e seed rodados com `-W always::DeprecationWarning` e testes em processo com DeprecationWarning como erro: nenhum warning | resolvido |
| F15 Magic numbers | LOW | PB-12 | nenhuma | grep dos literais (3/200, 1/5, `<= 2`, 7 dias, senha mínima, `#000000`, porta, listas de status/roles) fora de config/ sem ocorrências | resolvido |
| F16 Nomes ruins | LOW | PB-12 | nenhuma | grep de `p1..p5`, `for u/t/c in`, `cat =`, `d = {` sem ocorrências | resolvido |
| F17 Código morto / deps | LOW | PB-14 | nenhuma | pyflakes sem imports não usados (exceto o import intencional de `models` em database.py para registrar tabelas); funções mortas de helpers/models removidas; marshmallow e requests removidos; python-dotenv em uso | resolvido |
| F18 print como logging | LOW | PB-14 | nenhuma | grep `print(` na aplicação sem ocorrências (só no script seed.py); logging com LOG_LEVEL | resolvido |

## Intentional contract changes

- **Autenticação obrigatória (F01, regra 2):** 19 rotas passam a exigir `Authorization: Bearer <token>` (401 sem token, 403 sem papel). Públicas: `GET /`, `GET /health` e `POST /login` — esta última é a **exceção por emitir a credencial**.
- **Autorização por papel (F01):** `GET /users` e `GET /reports/summary` → admin/manager; `POST /users`, `DELETE /users/<id>` → admin; `GET /users/<id>`, `GET /users/<id>/tasks`, `GET /reports/user/<id>` → próprio usuário ou admin/manager; `PUT /users/<id>` → próprio usuário ou admin, e só admin altera `role`/`active`; `POST/PUT/DELETE /categories` → admin/manager.
- **Campo `password` removido** das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` (F02).
- **Token do login** agora é assinado e expira (padrão 8 h); a chave `token` continua na resposta (F05).
- **Senha mínima de 8 caracteres** em `POST /users` e `PUT /users/<id>`; senhas do seed trocadas para `joao1234`, `maria1234`, `pedro1234` (F03).
- **Entradas inválidas que davam 500/HTML agora dão 400 JSON**; body ausente/não-JSON dá 400 em vez de 415; 404/405 em JSON (F08, F09).
- **Bind padrão em 127.0.0.1** (era 0.0.0.0) e CORS só para origens de `CORS_ORIGINS` (F06). Porta 5000 e comando `python app.py` preservados.

## Validation

```
  ✓ Application boots without errors (`python app.py`)
  ✓ All endpoints respond correctly (22/22 match baseline)
  ✓ Every finding's impact no longer reproduces (18/18 findings)
  ✓ Every route cited in auth/exposure findings or CRITICAL findings requires credentials (19/19, except the login route)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
```

Os 22 status são idênticos ao baseline; as chaves de topo também, exceto `password` removido em 3 respostas de usuário (mudança intencional do F02).

| Método | Path | Status antes | Status depois (sem token) | Status depois (com token) |
|---|---|---|---|---|
| GET | `/` | 200 | — (pública) | 200 |
| GET | `/health` | 200 | — (pública) | 200 |
| GET | `/tasks` | 200 | 401 | 200 |
| GET | `/tasks/<int:task_id>` | 200 | 401 | 200 |
| GET | `/tasks/search` | 200 | 401 | 200 |
| GET | `/tasks/stats` | 200 | 401 | 200 |
| POST | `/tasks` | 201 | 401 | 201 |
| PUT | `/tasks/<int:task_id>` | 200 | 401 | 200 |
| GET | `/users` | 200 | 401 | 200 |
| GET | `/users/<int:user_id>` | 200 | 401 | 200 |
| POST | `/users` | 201 | 401 | 201 |
| PUT | `/users/<int:user_id>` | 200 | 401 | 200 |
| GET | `/users/<int:user_id>/tasks` | 200 | 401 | 200 |
| POST | `/login` | 200 | — (pública, emite credencial) | 200 |
| GET | `/reports/summary` | 200 | 401 | 200 |
| GET | `/reports/user/<int:user_id>` | 200 | 401 | 200 |
| GET | `/categories` | 200 | 401 | 200 |
| POST | `/categories` | 201 | 401 | 201 |
| PUT | `/categories/<int:cat_id>` | 200 | 401 | 200 |
| DELETE | `/tasks/<int:task_id>` | 200 | 401 | 200 |
| DELETE | `/categories/<int:cat_id>` | 200 | 401 | 200 |
| DELETE | `/users/<int:user_id>` | 200 | 401 | 200 |

Recomendações residuais (fora do Impact/Routes de qualquer finding): rate limiting no `POST /login`; controle de propriedade de tasks (hoje qualquer usuário autenticado edita qualquer task, como no time compartilhado original); servidor WSGI de produção no lugar do servidor de desenvolvimento do Flask.

```
================================
```
