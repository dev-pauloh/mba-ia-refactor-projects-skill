```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── .env.example
├── README.md
├── api.http
├── package.json                      # scripts.start inalterado: node src/app.js
├── docs/
│   ├── audit-report.md
│   └── refactor-summary.md
└── src/
    ├── app.js                        # composition root (DI, rotas, error handler, listen)
    ├── errors.js                     # AppError, ValidationError, PaymentDeclinedError, UnauthorizedError, NotFoundError
    ├── config/
    │   ├── index.js                  # process.env (+ .env opcional via process.loadEnvFile)
    │   └── constants.js              # PAYMENT_STATUS, APPROVED_CARD_PREFIX, DEFAULT_PORT...
    ├── database/
    │   ├── connection.js             # wrapper Promise do sqlite3 + transaction() serializada
    │   └── schema.js                 # schema com FOREIGN KEY + seed idempotente (senha com hash)
    ├── models/
    │   ├── userModel.js
    │   ├── courseModel.js            # inclui a query única (JOIN) do relatório
    │   ├── enrollmentModel.js
    │   ├── paymentModel.js
    │   └── auditLogModel.js
    ├── services/
    │   ├── checkoutService.js        # caso de uso de checkout (transação)
    │   ├── paymentGateway.js         # aprovação do pagamento, log mascarado
    │   ├── reportService.js          # agregação do relatório financeiro
    │   └── userService.js            # exclusão de usuário em cascata (transação)
    ├── validators/
    │   └── checkoutValidator.js
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── routes/
    │   ├── checkoutRoutes.js
    │   ├── adminRoutes.js
    │   └── userRoutes.js
    ├── middlewares/
    │   ├── asyncHandler.js
    │   ├── auth.js                   # requireAdmin (Authorization: Bearer <ADMIN_API_TOKEN>)
    │   └── errorHandler.js
    └── utils/
        ├── logger.js                 # níveis via LOG_LEVEL
        └── password.js               # scrypt + salt + timingSafeEqual

## Findings addressed
| ID | Sev. | Padrão | Rotas tratadas | Como o impacto foi verificado | Status |
|---|---|---|---|---|---|
| F01 | CRITICAL | PB-13 | GET /api/admin/financial-report, DELETE /api/users/:id (auth: Bearer ADMIN_API_TOKEN) | Sem token, com token errado ou sem "Bearer": 401 nas 2 rotas. Com token: 200. Boot sem ADMIN_API_TOKEN: 401 mesmo com header (falha fechada). A query não seleciona mais `email` | resolvido |
| F02 | CRITICAL | PB-01 | nenhuma | grep AP-01 e `pk_live_/admin_master/senha_super` com 0 ocorrências. Chave e porta lidas do env/.env (teste com .env: 200, sem warning). .env.example criado | resolvido |
| F03 | CRITICAL | PB-06 | POST /api/checkout (exceção: rota emissora de credencial) | Log pós-checkout mostra só "cartão final 4444" (sem PAN e sem chave). grep de log de cartão/chave com 0 ocorrências | resolvido |
| F04 | CRITICAL | PB-06 | POST /api/checkout (exceção: rota emissora de credencial) | Banco: seed e checkout gravam `salt(32hex):scrypt(128hex)`. verifyPassword('123') ok, '123456' falha. Checkout sem `pwd`: 400. grep badCrypto/base64/123456 com 0 ocorrências | resolvido |
| F05 | CRITICAL | PB-03 | nenhuma | AppManager.js/utils.js removidos. Nenhum arquivo combina rota e SQL. SQL só em models/ e database/ | resolvido |
| F06 | HIGH | PB-13 | POST /api/checkout (auth: senha da conta para e-mail existente) | E-mail do seed com senha errada: 401 e relatório inalterado (nada gravado). Sem pwd: 400. Senha correta: 200 | resolvido |
| F07 | HIGH | PB-12 | POST /api/checkout | `card` numérico, e-mail inválido, `c_id:"abc"`, cartão inválido, `usr` objeto e JSON malformado: 400. O servidor continuou respondendo (antes: crash) | resolvido |
| F08 | HIGH | PB-04 | POST /api/checkout, GET /api/admin/financial-report | Regra em CheckoutService/PaymentGateway/ReportService. grep startsWith/`revenue +=` em controllers/routes com 0 ocorrências. Rotas de 1 linha | resolvido |
| F09 | HIGH | PB-08 | POST /api/checkout, GET /api/admin/financial-report | grep `self = this`, `Pending--`, `function(err` com 0 ocorrências. Fluxo async/await + asyncHandler | resolvido |
| F10 | HIGH | PB-05 | POST /api/checkout | grep globalCache/logAndCache/totalRevenue/`^let` com 0 ocorrências | resolvido |
| F11 | HIGH | PB-05 | nenhuma | `sqlite3` só em database/connection.js. Database.open no app.js injetado em models → services → controllers. Gateway injetado (testes usaram fakes) | resolvido |
| F12 | MEDIUM | PB-10 | POST /api/checkout, DELETE /api/users/:id, GET /api/admin/financial-report | Falha forçada na auditoria fez rollback total (contagens iguais). FK rejeita matrícula órfã. Após DELETE /api/users/1, o relatório não mostra "Unknown" nem receita do usuário removido | resolvido |
| F13 | MEDIUM | PB-09 | POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id | Erro de banco no checkout propaga (não vira 404). Exceção em handler responde 500 "Erro interno" sem detalhes. Mensagens 400/404 em texto mantidas | resolvido |
| F14 | MEDIUM | PB-07 | GET /api/admin/financial-report | Contador de queries: relatório com 22 matrículas executa 1 query | resolvido |
| F15 | LOW | PB-12 | nenhuma | grep de "PAID"/"DENIED"/startsWith("4")/3000 fora de constants.js com 0 ocorrências | resolvido |
| F16 | LOW | PB-12 | nenhuma | grep u/e/p/cid/cc/enr/badCrypto com 0 ocorrências. Campos do contrato mapeados no validator | resolvido |
| F17 | LOW | PB-14 | nenhuma | grep dbUser/dbPass/smtpUser/totalRevenue e `email` no relatório com 0 ocorrências | resolvido |
| F18 | LOW | PB-14 | nenhuma | grep console.* com 0 ocorrências. Logger com níveis/LOG_LEVEL | resolvido |
| F19 | LOW | PB-11 | nenhuma | Callbacks do sqlite3 só dentro do wrapper database/connection.js | resolvido |

## Intentional contract changes
1. GET /api/admin/financial-report e DELETE /api/users/:id exigem `Authorization: Bearer <ADMIN_API_TOKEN>`. Sem token ou com token inválido respondem 401 "Não autorizado" (F01).
2. POST /api/checkout: exceção da regra de autenticação por ser a rota que emite a credencial (cria a conta e a senha do aluno). Continua pública para e-mails novos. Para e-mail já cadastrado, `pwd` precisa conferir, senão 401 "Credenciais inválidas" (F06).
3. POST /api/checkout: `pwd` passou a ser obrigatório e a validação ficou mais estrita (e-mail, c_id inteiro positivo, cartão com 13-19 dígitos). Entradas inválidas dão 400 em vez de 200 com senha padrão ou crash (F04, F07). JSON malformado dá 400 "Bad Request" em texto.
4. POST /api/checkout com pagamento recusado não cria mais a conta do usuário (sem gravação parcial). O status 400 não mudou (F12).
5. DELETE /api/users/:id remove em cascata as matrículas e os pagamentos do usuário. O corpo de texto passou a ser "Usuário deletado", porque a mensagem antiga dizia que deixava dados sujos (F12).

## Validation
  ✓ Application boots without errors (`npm start` → `node src/app.js`)
  ✓ All endpoints respond correctly (6/6 match baseline)
  ✓ Every finding's impact no longer reproduces (19/19 findings)
  ✓ Every route cited in auth/exposure findings or CRITICAL findings requires credentials (3/3: 2 rotas com Bearer de admin + POST /api/checkout como rota emissora de credencial, que exige senha para contas existentes)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
| Método | Path / cenário | Status antes | Status depois |
|---|---|---|---|
| POST | /api/checkout (sucesso) | 200 | 200 |
| POST | /api/checkout (pagamento recusado) | 400 | 400 |
| POST | /api/checkout (campos faltando) | 400 | 400 |
| POST | /api/checkout (curso inexistente) | 404 | 404 |
| GET | /api/admin/financial-report (com token) | 200 | 200 |
| DELETE | /api/users/1 (com token) | 200 | 200 |
| GET | /api/admin/financial-report (sem token) | 200 | 401 |
| DELETE | /api/users/1 (sem token) | 200 | 401 |
| POST | /api/checkout (e-mail existente, senha errada) | 200 | 401 |
| POST | /api/checkout (`card` numérico) | crash do processo | 400 |
================================
```
