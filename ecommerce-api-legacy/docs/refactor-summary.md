```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── package.json                  # scripts.start inalterado: node src/app.js
├── .env.example
├── README.md
├── api.http
├── docs/
│   ├── audit-report.md
│   └── refactor-summary.md
└── src/
    ├── app.js                    # composition root: db, models, controllers, rotas, error handler, listen
    ├── errors.js                 # AppError, ValidationError, UnauthorizedError, NotFoundError, PaymentDeclinedError
    ├── config/
    │   ├── index.js              # config via process.env (segredos nunca literais)
    │   └── constants.js          # PaymentStatus, APPROVED_CARD_PREFIX
    ├── database/
    │   ├── connection.js         # wrapper Promise sobre sqlite3 + transaction() serializada
    │   └── schema.js             # schema com FKs + seed idempotente com senha em scrypt
    ├── models/
    │   ├── userModel.js
    │   ├── courseModel.js        # inclui query única (LEFT JOIN) do relatório
    │   ├── enrollmentModel.js
    │   ├── paymentModel.js
    │   └── auditLogModel.js
    ├── services/
    │   └── paymentService.js     # gateway simulado, chave injetada, log só com final do cartão
    ├── controllers/
    │   ├── checkoutController.js # validação + fluxo do checkout em transação
    │   ├── reportController.js   # agregação de receita
    │   └── userController.js     # delete com dependentes em transação
    ├── routes/                   # camada View (express.Router)
    │   ├── checkoutRoutes.js
    │   ├── adminRoutes.js
    │   └── userRoutes.js
    ├── middlewares/
    │   ├── asyncHandler.js
    │   ├── auth.js               # X-Admin-Token vs ADMIN_TOKEN (timingSafeEqual)
    │   └── errorHandler.js       # erro central, mantém formato texto
    └── utils/
        ├── logger.js
        └── password.js           # hashPassword / verifyPassword (crypto.scrypt + salt)

## Findings addressed
| Finding | Severidade | Padrão aplicado | Status |
|---|---|---|---|
| F01 Hardcoded credentials | CRITICAL | PB-01 | Resolvido: config/index.js lê env; dbUser/dbPass/smtpUser removidos |
| F02 Cartão e chave em log | CRITICAL | PB-06 | Resolvido: log só com os 4 últimos dígitos; chave nunca logada |
| F03 Hash fraco / senha padrão | CRITICAL | PB-06 | Resolvido: scrypt + salt; seed com hash; sem senha padrão "123456" |
| F04 Endpoints admin sem auth | CRITICAL | PB-13 | Resolvido: middleware requireAdmin nas duas rotas |
| F05 God Class AppManager | CRITICAL | PB-03 | Resolvido: AppManager.js e utils.js removidos, camadas MVC |
| F06 Regra de negócio na rota | HIGH | PB-04 | Resolvido: regras em controllers/service; rotas só delegam |
| F07 Callback hell | HIGH | PB-08 | Resolvido: async/await sobre wrapper Promise |
| F08 Estado global mutável | HIGH | PB-05 | Resolvido: globalCache/totalRevenue removidos (nunca lidos) |
| F09 Acoplamento sem DI | HIGH | PB-05 | Resolvido: db e services injetados via construtor no composition root |
| F10 N+1 no relatório | MEDIUM | PB-07 | Resolvido: 1 query com LEFT JOIN + agregação em memória |
| F11 Sem transação / órfãos | MEDIUM | PB-10 | Resolvido: checkout e delete em transação; FKs + PRAGMA foreign_keys |
| F12 Validação fraca | MEDIUM | PB-12 | Resolvido: tipos/formatos validados; JSON inválido → 400 |
| F13 Erros engolidos | MEDIUM | PB-09 | Resolvido: asyncHandler + errorHandler central |
| F14 Magic numbers/strings | LOW | PB-12 | Resolvido: PaymentStatus, APPROVED_CARD_PREFIX, porta via env |
| F15 Nomenclatura ruim | LOW | PB-12 | Resolvido internamente; campos do contrato (usr, eml...) mantidos na borda |
| F16 Código morto | LOW | PB-14 | Resolvido |
| F17 console.log como logging | LOW | PB-14 | Resolvido: utils/logger.js com níveis |
| F18 API callback do sqlite3 | LOW | PB-11, PB-08 | Resolvido: wrapper Promise em database/connection.js |

## Intentional contract changes
- GET /api/admin/financial-report e DELETE /api/users/:id exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN`; sem ele (ou com ADMIN_TOKEN não definida) respondem 401 "Não autorizado" (F04).
- POST /api/checkout: `pwd` passa a ser obrigatório quando o checkout cria um usuário novo (antes era usado "123456"). Sem ele responde 400 (F03).
- POST /api/checkout: entradas malformadas (card não-string, email inválido, c_id não inteiro, JSON inválido) respondem 400 em vez de derrubar o processo ou devolver 500 (F12).
- DELETE /api/users/:id: id inexistente → 404 e id não numérico → 400 (antes era sempre 200). O texto de sucesso passou a ser "Usuário deletado.". As matrículas e pagamentos do usuário são removidos na mesma transação, por isso o relatório deixa de mostrar alunos "Unknown" (F11, F13).
- Checkout com pagamento recusado não cria mais a conta do usuário (antes o usuário era gravado antes da cobrança).

## Validation
  ✓ Application boots without errors (`npm start`)
  ✓ All endpoints respond correctly (8/8 match baseline)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
| Método | Path | Caso | Status antes | Status depois |
|---|---|---|---|---|
| POST | /api/checkout | sucesso, usuário novo | 200 | 200 |
| POST | /api/checkout | sucesso, usuário existente | 200 | 200 |
| POST | /api/checkout | pagamento recusado | 400 | 400 |
| POST | /api/checkout | campo ausente | 400 | 400 |
| POST | /api/checkout | curso inexistente | 404 | 404 |
| GET | /api/admin/financial-report | com X-Admin-Token | 200 | 200 |
| DELETE | /api/users/1 | com X-Admin-Token | 200 | 200 |
| GET | /api/admin/financial-report | após delete | 200 | 200 |
================================
```
