```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── app.py                         # composition root create_app() + lançador (python app.py)
├── database.py                    # instância SQLAlchemy
├── seed.py                        # seed manual (usa create_app)
├── requirements.txt
├── .env.example
├── README.md
├── config/
│   ├── settings.py                # Settings lidas do ambiente/.env
│   └── constants.py               # status, prioridades, roles, limites
├── models/                        # Model: entidades + todo o acesso a dados
│   ├── base.py                    # BaseModel (get_by_id, save, delete, count) + commit()
│   ├── task.py
│   ├── user.py
│   └── category.py
├── controllers/                   # Controller: validação + regras de negócio
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── routes/                        # View: blueprints HTTP finos
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py
│   ├── report_routes.py
│   └── system_routes.py           # / e /health
├── middlewares/
│   ├── error_handler.py           # AppError + handlers centrais
│   └── auth.py                    # Bearer token, require_admin
├── services/
│   ├── token_service.py           # tokens assinados (itsdangerous)
│   └── notification_service.py    # SMTP com config injetada, sem estado
├── utils/
│   └── helpers.py                 # utcnow, percentual, validadores, parse
└── docs/
    ├── audit-report.md
    └── refactor-summary.md

## Findings addressed
| Finding | Severity | Pattern | Status |
|---|---|---|---|
| F01 Hardcoded credentials | CRITICAL | PB-01 | Fixed — SECRET_KEY/SMTP_* vêm do ambiente (.env via python-dotenv); chave aleatória + warning se ausente |
| F02 MD5 password hash | CRITICAL | PB-06 | Fixed — werkzeug generate/check_password_hash; seed re-hasheado |
| F03 Password hash nas respostas | CRITICAL | PB-06 | Fixed — User.to_dict sem password |
| F04 Endpoints admin sem auth | CRITICAL | PB-13 | Fixed para gestão de usuários (DELETE /users, role/active exigem admin). DELETE /tasks e /categories continuam abertos por serem CRUD comum chamado sem credenciais (mvc-guidelines §6.5) — risco residual |
| F05 Token falso | HIGH | PB-13 | Fixed — token assinado com SECRET_KEY e expiração, verificado pelo middleware auth |
| F06 debug/0.0.0.0/CORS aberto | HIGH | PB-01 | Fixed — DEBUG=false, HOST=127.0.0.1, CORS só para CORS_ORIGINS |
| F07 Fat routes | HIGH | PB-04 | Fixed — controllers por domínio; rotas só delegam; categorias em blueprint próprio |
| F08 Acoplamento / sem factory / estado | HIGH | PB-05 | Fixed — create_app(); serviços instanciados e injetados no composition root; lista de notificações em memória removida |
| F09 N+1 e contagens repetidas | MEDIUM | PB-07 | Fixed — joinedload em /tasks; GROUP BY em status, prioridade, usuários e categorias |
| F10 Integridade na exclusão | MEDIUM | PB-10 | Fixed — cascade de tasks declarado no model; Category.delete desvincula tasks na mesma transação. Obs.: na verificação o ORM já anulava category_id via backref, então a parte de "tasks órfãs" do finding era imprecisa; a regra agora está explícita |
| F11 Lógica duplicada | MEDIUM | PB-12 | Fixed — Task.is_overdue único; to_dict/to_summary_dict; validadores únicos para create/update |
| F12 Validação fraca (500) | MEDIUM | PB-12 | Fixed — tipos validados, 400 em vez de 500 |
| F13 Error handling | MEDIUM | PB-09 | Fixed — handlers centrais; nenhum except vazio |
| F14 Magic numbers/strings | LOW | PB-12 | Fixed — config/constants.py |
| F15 Nomenclatura | LOW | PB-12 | Fixed — p1..p5 substituídos por PRIORITY_LABELS; nomes descritivos |
| F16 Código morto / deps | LOW | PB-14 | Fixed — imports e helpers mortos removidos; marshmallow e requests fora do manifesto; python-dotenv passou a ser usado |
| F17 print como log | LOW | PB-14 | Fixed — logging (print só no CLI seed.py) |
| F18 APIs deprecated | LOW | PB-11 | Fixed — db.session.get / select(); helper utcnow() com timezone.utc |

## Intentional contract changes
- `password` removido das respostas de GET /users/<id>, POST /users, PUT /users/<id> e POST /login (F03).
- POST /login: a chave `token` continua existindo, mas agora é um token assinado e com expiração, não `fake-jwt-token-<id>` (F05).
- DELETE /users/<id> exige `Authorization: Bearer <token>` de um admin → 401 sem token/token inválido, 403 se não for admin (F04).
- POST /users com `role` diferente de `user`, e PUT /users/<id> que altere `role` ou `active`, exigem token de admin → 403 caso contrário (F04).
- Entradas inválidas que antes geravam 500 agora geram 400 (priority não numérica, title null, search com priority/user_id não inteiros, PUT /categories sem corpo); `color` fora do formato #RRGGBB e `active` não booleano agora são rejeitados com 400 (F12).
- Erros (inclusive 404/405 do framework) sempre em JSON `{"error": ...}`; corpo JSON ausente ou malformado responde 400 "Dados inválidos".
- Defaults de ambiente: servidor em 127.0.0.1 (antes 0.0.0.0), debug desligado e CORS desabilitado até configurar CORS_ORIGINS (F06).
- A mensagem de data inválida no PUT /tasks passou a ser a mesma do POST ("Formato de data inválido. Use YYYY-MM-DD").

Riscos residuais / recomendações: DELETE /tasks e DELETE /categories e as demais escritas continuam sem autenticação para não quebrar clientes; recomenda-se exigir token nelas quando os clientes estiverem prontos. Defina SECRET_KEY no ambiente para que os tokens sobrevivam a reinícios.

## Validation
  ✓ Application boots without errors (`python app.py`)
  ✓ All endpoints respond correctly (26/26 match baseline)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (DELETE /tasks e /categories sem auth ficam como risco residual intencional, ver F04)

| Method | Path | Status before | Status after |
|---|---|---|---|
| GET | / | 200 | 200 |
| GET | /health | 200 | 200 |
| GET | /tasks | 200 | 200 |
| GET | /tasks/1 | 200 | 200 |
| GET | /tasks/999 | 404 | 404 |
| POST | /tasks | 201 | 201 |
| POST | /tasks (title curto) | 400 | 400 |
| PUT | /tasks/11 | 200 | 200 |
| GET | /tasks/search?q=API&status=pending | 200 | 200 |
| GET | /tasks/stats | 200 | 200 |
| GET | /users | 200 | 200 |
| GET | /users/1 | 200 | 200 (sem `password`) |
| POST | /users | 201 | 201 (sem `password`) |
| POST | /users (email duplicado) | 409 | 409 |
| PUT | /users/4 | 200 | 200 (sem `password`) |
| GET | /users/1/tasks | 200 | 200 |
| POST | /login | 200 | 200 (token assinado) |
| POST | /login (senha errada) | 401 | 401 |
| GET | /reports/summary | 200 | 200 |
| GET | /reports/user/1 | 200 | 200 |
| GET | /categories | 200 | 200 |
| POST | /categories | 201 | 201 |
| PUT | /categories/5 | 200 | 200 |
| DELETE | /tasks/11 | 200 | 200 |
| DELETE | /categories/5 | 200 | 200 |
| DELETE | /users/4 | 200 | 200 (com token admin; 401 sem token) |
================================
```
