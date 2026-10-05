```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── app.py                         # composition root: create_app() + start (python app.py)
├── database.py                    # extensão SQLAlchemy
├── seed.py                        # seed (python seed.py), usa create_app()
├── requirements.txt
├── .env.example
├── README.md
├── config/
│   ├── settings.py                # Settings via env/.env (SECRET_KEY, DB, DEBUG, HOST, PORT, CORS, SMTP, token)
│   └── constants.py               # status, prioridades, limites, roles, cor padrão
├── models/                        # Model: ORM + consultas + regras da entidade
│   ├── task.py                    # is_overdue, to_dict, search, GROUP BY, detach_category
│   ├── user.py                    # hash werkzeug, to_dict sem password
│   └── category.py
├── controllers/                   # casos de uso, validação, autorização por recurso
│   ├── task_controller.py
│   ├── user_controller.py         # inclui login
│   ├── category_controller.py
│   ├── report_controller.py
│   └── validation.py              # validadores compartilhados
├── routes/                        # View: blueprints finos
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py
│   ├── report_routes.py
│   └── system_routes.py           # GET /, GET /health
├── middlewares/
│   ├── auth.py                    # require_auth(admin=...) com Bearer token
│   └── error_handler.py           # AppError/ValidationError/... + handlers JSON
├── services/
│   ├── token_service.py           # token assinado (itsdangerous) com expiração
│   └── notification_service.py    # SMTP configurável, sem estado, injetado
├── utils/
│   └── helpers.py                 # utcnow, percentage, is_valid_email, is_valid_color
└── docs/
    ├── audit-report.md
    └── refactor-summary.md

## Findings addressed
| Finding | Sev. | Padrão | Status |
|---|---|---|---|
| F01 Segredos hardcoded | CRITICAL | PB-01 | Resolvido: SECRET_KEY/SMTP em config/settings.py via env (aleatória + warning se ausente); .env.example. Routes: nenhuma |
| F02 Senha MD5 | CRITICAL | PB-06, PB-13 | Resolvido: werkzeug scrypt. POST /users → Bearer + admin; PUT /users/<id> → Bearer (próprio ou admin); POST /login → exceção: emite credencial |
| F03 Hash na resposta | CRITICAL | PB-06, PB-13 | Resolvido: password fora de to_dict. GET /users/<id> → Bearer (próprio ou admin); POST /users → Bearer + admin; PUT /users/<id> → Bearer (próprio ou admin); POST /login → exceção: emite credencial |
| F04 Endpoints sem auth | CRITICAL | PB-13 | Resolvido: GET /users, POST /users, DELETE /users/<id>, GET /reports/summary → Bearer + admin; PUT /users/<id>, GET /reports/user/<id> → Bearer (próprio ou admin; role/active só admin); DELETE /tasks/<id>, DELETE /categories/<id> → Bearer |
| F05 God File report_routes | CRITICAL | PB-03, PB-04, PB-13 | Resolvido: reports e categories separados em routes + controllers. GET /reports/summary → Bearer + admin; GET /reports/user/<id> → Bearer (próprio ou admin); GET /categories, POST /categories, PUT /categories/<id>, DELETE /categories/<id> → Bearer |
| F06 Token falso | HIGH | PB-13 | Resolvido: TokenService (itsdangerous, TOKEN_MAX_AGE) + middleware require_auth |
| F07 Fat routes | HIGH | PB-04 | Resolvido: handlers de 2-5 linhas delegando a controllers |
| F08 Debug/CORS | HIGH | PB-01 | Resolvido: FLASK_DEBUG=false, HOST=127.0.0.1, CORS só para CORS_ORIGINS |
| F09 Estado em memória | HIGH | PB-05 | Resolvido: lista notifications e get_notifications removidas; serviço sem estado |
| F10 Acoplamento | HIGH | PB-05 | Resolvido: create_app(settings) monta tudo; controllers recebem serviços no construtor; NotificationService.from_config |
| F11 N+1 | MEDIUM | PB-07 | Resolvido: joinedload em GET /tasks; GROUP BY em stats, summary, users e categories |
| F12 Duplicação | MEDIUM | PB-12 | Resolvido: Task.is_overdue único, validate_task_payload para create/update, constants.py, controllers/validation.py |
| F13 Validação fraca | MEDIUM | PB-12 | Resolvido: tipos validados → 400 (priority, title, ids, query args, body, color, active, name) |
| F14 Error handling | MEDIUM | PB-09 | Resolvido: error handler central JSON com rollback; zero except: sem tipo |
| F15 Órfãos de categoria | MEDIUM | PB-10 | Resolvido: tasks desassociadas na mesma transação do DELETE |
| F16 APIs deprecated | MEDIUM | PB-11 | Resolvido: db.session.get / db.select; utcnow() via datetime.now(timezone.utc) |
| F17 Magic numbers | LOW | PB-12 | Resolvido: config/constants.py |
| F18 Nomenclatura | LOW | PB-12 | Resolvido: p1..p5 → PRIORITY_LABELS; parâmetros renomeados |
| F19 Código morto | LOW | PB-14 | Resolvido: imports, métodos e helpers mortos removidos; marshmallow/requests fora do requirements; python-dotenv passou a ser usado |
| F20 print | LOW | PB-14 | Resolvido: logging (print mantido só no CLI seed.py) |

## Intentional contract changes
- Campo `password` removido das respostas de GET /users/<id>, POST /users, PUT /users/<id> e de `user` em POST /login.
- Autenticação `Authorization: Bearer <token>` (401 sem/inválido, 403 sem permissão) em todas as rotas citadas nos findings CRITICAL: GET /users, GET /users/<id>, POST /users, PUT /users/<id>, DELETE /users/<id>, DELETE /tasks/<id>, GET /reports/summary, GET /reports/user/<id>, GET /categories, POST /categories, PUT /categories/<id>, DELETE /categories/<id>.
- Admin exigido em GET /users, POST /users, DELETE /users/<id> e GET /reports/summary; nas rotas de usuário/relatório individual, só o próprio usuário ou admin; apenas admin altera `role`/`active`.
- Exceção: POST /login continua público (emite a credencial). A chave `token` foi mantida, agora assinada e com expiração; tokens `fake-jwt-token-<id>` são rejeitados.
- Entradas inválidas que davam 500 agora dão 400; `color` precisa ser #RRGGBB; `name` não pode ser vazio; `active` precisa ser booleano.
- 404/405/500 sempre em JSON `{"error": ...}`; falhas inesperadas retornam a mensagem genérica "Erro interno".
- Padrões de execução seguros: debug desligado, HOST 127.0.0.1 e CORS desabilitado até `CORS_ORIGINS` ser definido (porta continua 5000).
- DELETE /categories/<id> zera `category_id` das tasks associadas.
- Atribuir uma task a um usuário dispara NotificationService (só registra em log enquanto SMTP_HOST não estiver configurado).
- Recomendação residual: continuam públicas, por não serem citadas em finding CRITICAL, GET/POST /tasks, GET/PUT /tasks/<id>, GET /tasks/search, GET /tasks/stats e GET /users/<id>/tasks. Avaliar exigir auth nelas.

## Validation
  ✓ Application boots without errors (`python app.py`, sem traceback nem DeprecationWarning)
  ✓ All endpoints respond correctly (22/22 match baseline; diferença de chaves só na remoção de `password`)
  ✓ Every route cited in CRITICAL findings requires credentials (12/12 com 401 sem token e status do baseline com token; POST /login é a exceção)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (greps de AP-01/03/04/05/06/07/08/09/10/12 sem ocorrências)
| Método | Path | Antes | Depois sem token | Depois com token |
|---|---|---|---|---|
| GET | / | 200 | 200 | 200 |
| GET | /health | 200 | 200 | 200 |
| POST | /login | 200 | 200 | 200 |
| GET | /tasks | 200 | 200 | 200 |
| GET | /tasks/1 | 200 | 200 | 200 |
| GET | /tasks/search?q=API&status=pending | 200 | 200 | 200 |
| GET | /tasks/stats | 200 | 200 | 200 |
| GET | /users | 200 | 401 | 200 |
| GET | /users/1 | 200 | 401 | 200 |
| GET | /users/1/tasks | 200 | 200 | 200 |
| GET | /reports/summary | 200 | 401 | 200 |
| GET | /reports/user/1 | 200 | 401 | 200 |
| GET | /categories | 200 | 401 | 200 |
| POST | /users | 201 | 401 | 201 |
| PUT | /users/4 | 200 | 401 | 200 |
| POST | /tasks | 201 | 201 | 201 |
| PUT | /tasks/11 | 200 | 200 | 200 |
| POST | /categories | 201 | 401 | 201 |
| PUT | /categories/5 | 200 | 401 | 200 |
| DELETE | /tasks/11 | 200 | 401 | 200 |
| DELETE | /categories/5 | 200 | 401 | 200 |
| DELETE | /users/4 | 200 | 401 | 200 |
Extra: 403 para não-admin (GET /users, GET /users/1, POST /users, PUT role, GET /reports/summary); 400 para priority/title/query/body/cor inválidos; token forjado → 401; DELETE de categoria sem órfãos; hash scrypt no banco.
================================
```
