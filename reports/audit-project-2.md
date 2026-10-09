# Audit Report — Projeto 2: ecommerce-api-legacy (Node.js/Express)

> Saída da Fase 2 da skill `/refactor-arch`, executada em `ecommerce-api-legacy/` (Claude Code 2.1.284, Opus 5.5). Execução com a versão final da skill (recomendação cobre todo o impacto de cada finding).

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 22) + Express ^4.18.2 (4.22.1)
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-09

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 3 | LOW: 5

## Findings

### F01 [CRITICAL] Endpoints administrativos sem autenticação (AP-05)
File: src/AppManager.js:80-129, 131-137
Description: GET /api/admin/financial-report devolve o faturamento por curso e a lista de alunos com o valor pago por cada um. DELETE /api/users/:id executa "DELETE FROM users WHERE id = ?". Nenhuma das duas rotas tem middleware ou checagem de identidade/permissão, e não existe nenhum mecanismo de auth no projeto. A query do relatório ainda seleciona `email` dos usuários (:104). Routes: GET /api/admin/financial-report, DELETE /api/users/:id
Impact: qualquer cliente anônimo lê o faturamento da plataforma e os nomes e valores pagos de todos os alunos, e apaga qualquer usuário por id.
Recommendation: criar o middleware `requireAdmin`, que exige `Authorization: Bearer <token>` comparado em tempo constante (crypto.timingSafeEqual) com ADMIN_API_TOKEN lido do ambiente. Ele falha fechado (401 se a variável não estiver definida) e é aplicado a GET /api/admin/financial-report e DELETE /api/users/:id, respondendo 401 sem token ou com token inválido. A query do relatório deixa de buscar `email` (PB-13).

### F02 [CRITICAL] Segredos hardcoded no código (AP-01)
File: src/utils.js:1-7
Description: o objeto exportado `config` contém dbUser "admin_master", dbPass "senha_super_secreta_prod_123", paymentGatewayKey "pk_live_1234567890abcdef" (prefixo de chave de produção), smtpUser e a porta 3000 como literais. Ele é importado por src/app.js:3 e src/AppManager.js:2. Routes: nenhuma (o vazamento da chave via log está em F03)
Impact: qualquer pessoa com acesso ao repositório obtém a chave live do gateway de pagamento e a senha de banco, e trocar esses valores exige alterar código e fazer deploy.
Recommendation: criar src/config/index.js lendo PAYMENT_GATEWAY_KEY e PORT de process.env (carregando `.env` opcional via process.loadEnvFile, da stdlib) e publicar um .env.example sem valores reais. dbUser, dbPass e smtpUser saem do código, pois não são usados: o banco é SQLite em memória e não há SMTP (PB-01).

### F03 [CRITICAL] Número de cartão e chave do gateway gravados em log (AP-06)
File: src/AppManager.js:45
Description: cada checkout executa console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`), gravando o PAN completo e a chave live no stdout. POST /api/checkout é a rota pública que cadastra a conta e a senha do aluno (rota emissora de credencial), por isso continua acessível sem autenticação prévia para e-mails novos (ver F06). Routes: POST /api/checkout
Impact: qualquer pessoa com acesso aos logs (agregador, suporte, backup) obtém números de cartão completos e a chave do gateway. Isso viola o PCI-DSS.
Recommendation: remover o log. Registrar apenas o evento via logger com o cartão mascarado (últimos 4 dígitos) e sem a chave (PB-06).

### F04 [CRITICAL] Armazenamento de senha inseguro (AP-04)
File: src/utils.js:17-23
File: src/AppManager.js:18, 68-69
Description: badCrypto concatena 10000 vezes os 2 primeiros caracteres do base64 da senha e devolve 10 caracteres. É determinístico, sem salt, reversível na prática e com muitas colisões. O seed grava a senha '123' em texto puro (:18). Quando `pwd` está ausente, o checkout cria a conta com a senha padrão "123456" (:68). POST /api/checkout é a rota que cadastra credenciais (ver F03). Routes: POST /api/checkout
Impact: um vazamento do banco revela as senhas (ou colisões válidas) de todos os usuários. Contas criadas sem `pwd` ficam com a senha conhecida "123456".
Recommendation: criar src/utils/password.js com hashPassword/verifyPassword usando crypto.scrypt com salt aleatório e comparação timingSafeEqual. `pwd` passa a ser obrigatório no checkout (400 se ausente), o default "123456" é eliminado, o seed grava a senha já com hash e badCrypto é removido (PB-06).

### F05 [CRITICAL] God Class AppManager (AP-03)
File: src/AppManager.js:4-139
Description: a classe AppManager cria a conexão (:7), define o schema e o seed (:10-23), registra todas as rotas (:25-138) e, dentro delas, valida a entrada, decide a aprovação do pagamento, persiste em 4 tabelas, grava auditoria e monta o relatório financeiro. São 5 entidades e 3 camadas num único arquivo. Routes: nenhuma (impacto estrutural)
Impact: nada é testável isoladamente, qualquer mudança toca o mesmo arquivo e não há fronteira entre HTTP, regra de negócio e dados.
Recommendation: dividir em config/, database/ (conexão + schema/seed), models/ (user, course, enrollment, payment, auditLog), services/ (checkout, paymentGateway, report), controllers/, routes/ e middlewares/, deixando src/app.js apenas como composition root (PB-03).

### F06 [HIGH] Checkout usa conta existente sem verificar a senha (AP-12)
File: src/AppManager.js:40, 66-75
Description: quando o e-mail informado já existe, o handler chama processPaymentAndEnroll(user.id) sem comparar `pwd` com a senha armazenada. `pwd` e `usr` são ignorados. Routes: POST /api/checkout
Impact: quem conhece o e-mail de um aluno cria matrículas e pagamentos na conta dele e gera registros de auditoria falsamente atribuídos a ele. A identidade nunca é verificada.
Recommendation: no checkout, se o e-mail existir, verificar `pwd` com verifyPassword contra o hash armazenado e responder 401 sem gravar nada em caso de divergência. E-mail novo segue criando a conta com senha em hash (PB-13).

### F07 [HIGH] Validação de entrada fraca derruba o processo (AP-16)
File: src/AppManager.js:29-35, 46
Description: o checkout só checa presença (`if (!u || !e || !cid || !cc)`). Com `"card": 4111` (número), `cc.startsWith("4")` lança TypeError dentro do callback do sqlite3. Esse erro não passa pelo Express e vira uncaughtException, que encerra o processo. Formato de e-mail, tipo de c_id e formato do cartão não são validados. Severidade elevada de MEDIUM para HIGH porque uma única requisição anônima derruba a API inteira. Routes: POST /api/checkout
Impact: qualquer cliente derruba o servidor (negação de serviço) com um body de tipo inesperado. Dados malformados (e-mail inválido, c_id não numérico) chegam ao banco.
Recommendation: validar no controller/validator usr, eml (formato), pwd (strings não vazias), c_id (inteiro positivo) e card (string de 13-19 dígitos), respondendo 400 "Bad Request". Exceções inesperadas passam a ser capturadas pelo error handler central (F13), sem derrubar o processo (PB-12).

### F08 [HIGH] Regra de negócio dentro das rotas (AP-07)
File: src/AppManager.js:28-78, 80-129
Description: o handler de checkout decide a aprovação do pagamento (`cc.startsWith("4")`, :46), cria usuário, matrícula e pagamento, grava auditoria (:57) e cache (:59). O handler do relatório agrega a receita (`courseData.revenue += payment.amount`, :109) e monta a estrutura de resposta. Routes: POST /api/checkout, GET /api/admin/financial-report
Impact: as regras de pagamento e de faturamento só são testáveis via HTTP e não podem ser reutilizadas. Qualquer ajuste de regra exige mexer na camada HTTP.
Recommendation: mover a orquestração para CheckoutService.checkout (com PaymentGateway.charge para a aprovação) e ReportService.financialReport. Os controllers apenas extraem os dados do req e formatam a resposta (PB-04).

### F09 [HIGH] Callback hell e contadores manuais de pendência (AP-11)
File: src/AppManager.js:26, 37-77, 86-122
Description: o checkout encadeia 5 níveis de callbacks (db.get :37 → db.get :40 → db.run :50 → db.run :54 → db.run :57) e usa `const self = this` (:26) para escapar de `function`. O relatório usa os contadores coursesPending/enrPending (:86, :93, :97, :117, :120) e duplica o bloco de finalização (:96-98 e :119-121). Routes: POST /api/checkout, GET /api/admin/financial-report
Impact: um erro em qualquer nível não propaga (requisição pendurada ou crash, ex.: `enrollments.length` com `enrollments` undefined em :93). O fluxo é ilegível e não testável.
Recommendation: wrapper de Promise sobre o sqlite3 (run/get/all/exec) e services em async/await, com asyncHandler encaminhando rejeições ao error handler. Remover `self` e os contadores (PB-08).

### F10 [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-15, 25
File: src/AppManager.js:59
Description: `let globalCache = {}` é exportado e recebe `last_checkout_<userId>` a cada checkout (logAndCache), mas nunca é lido. `let totalRevenue = 0` é exportado e nunca atualizado. Routes: POST /api/checkout
Impact: o cache cresce sem limite a cada checkout (vazamento de memória proporcional ao número de usuários) e é compartilhado entre requisições, o que impede escalar horizontalmente.
Recommendation: remover globalCache, logAndCache e totalRevenue, sem estado mutável em nível de módulo. A conexão é criada no composition root e injetada (PB-05).

### F11 [HIGH] Acoplamento direto à infraestrutura (AP-09)
File: src/AppManager.js:7
File: src/app.js:8-10
Description: o construtor de AppManager instancia `new sqlite3.Database(':memory:')` e todos os handlers usam `this.db` diretamente. Não há como fornecer outro banco ou um gateway de pagamento falso. Routes: nenhuma
Impact: impossível testar com fakes ou trocar banco ou gateway sem reescrever a regra de negócio.
Recommendation: createDatabase() no composition root (src/app.js), injetado em models → services → controllers via factory/construtor. O gateway de pagamento também é injetado no CheckoutService (PB-05).

### F12 [MEDIUM] Escritas multi-etapa sem transação e dados órfãos (AP-14)
File: src/AppManager.js:12-16, 50-61, 69, 131-137
Description: o checkout grava users (:69), enrollments (:50), payments (:54) e audit_logs (:57) em comandos independentes, sem BEGIN/COMMIT/ROLLBACK. O DELETE apaga só o usuário e deixa matrículas e pagamentos órfãos (a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco"). O schema não declara FOREIGN KEY. Routes: POST /api/checkout, DELETE /api/users/:id, GET /api/admin/financial-report
Impact: uma falha parcial deixa usuário sem matrícula ou matrícula sem pagamento. Após um delete, o relatório passa a listar alunos "Unknown" e soma receita de usuários inexistentes.
Recommendation: executar o checkout em transação (BEGIN/COMMIT, ROLLBACK em qualquer erro). O DELETE apaga em transação os pagamentos das matrículas do usuário, as matrículas e o usuário. Declarar FOREIGN KEY no schema com PRAGMA foreign_keys = ON, para que o relatório não mostre mais órfãos (PB-10).

### F13 [MEDIUM] Erros engolidos e sem tratamento central (AP-17)
File: src/AppManager.js:38, 57-60, 92-93, 104-106, 133-135
File: src/app.js:1-14
Description: :38 trata erro de banco como 404 "Curso não encontrado". :57 ignora o erro da auditoria e responde sucesso. :92, :104 e :106 ignoram `err` (crash em `enrollments.length`). :133-135 ignora `err` do DELETE e sempre responde sucesso. Não existe middleware `(err, req, res, next)`. Routes: POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id
Impact: falhas de banco aparecem como 404 ou como sucesso falso, ou derrubam o processo. O cliente não distingue erro de sucesso.
Recommendation: classes AppError (Validation 400, Unauthorized 401, NotFound 404) e middleware central que responde o status e a mensagem do AppError ou 500 genérico ("Erro interno") sem detalhes. Todo erro de banco é propagado (500), 404 só quando o curso não existe e a falha de auditoria aborta a transação. Mensagens de erro em texto mantidas (PB-09).

### F14 [MEDIUM] Queries N+1 no relatório financeiro (AP-13)
File: src/AppManager.js:83, 92, 104, 106
Description: uma query de cursos, mais uma de matrículas por curso, mais duas (users e payments) por matrícula: 1 + C + 2E queries por requisição. Routes: GET /api/admin/financial-report
Impact: o tempo de resposta cresce linearmente com o número de matrículas.
Recommendation: uma única query courses LEFT JOIN enrollments LEFT JOIN users LEFT JOIN payments, com agregação em memória no ReportService (PB-07).

### F15 [LOW] Magic numbers e strings (AP-18)
File: src/AppManager.js:21, 46, 48, 68, 108
File: src/utils.js:6, 19-22
Description: aprovação de pagamento por `startsWith("4")`, status "PAID"/"DENIED" repetidos como strings soltas, senha padrão "123456", porta 3000 e os literais 10000/2/10 de badCrypto. Routes: nenhuma
Impact: a regra de aprovação e os status ficam espalhados e sujeitos a erro de digitação.
Recommendation: constantes nomeadas em src/config/constants.js (PAYMENT_STATUS, APPROVED_CARD_PREFIX, DEFAULT_PORT) e parâmetros de scrypt nomeados (PB-12).

### F16 [LOW] Nomenclatura ruim (AP-19)
File: src/AppManager.js:4, 29-33, 89, 102
File: src/utils.js:17
Description: variáveis u, e, p, cid, cc, c, enr; função badCrypto; classe genérica AppManager e módulo genérico utils.js. Routes: nenhuma
Impact: leitura difícil; nomes não revelam intenção.
Recommendation: nomes descritivos (userName, email, password, courseId, cardNumber). Os campos da API (usr, eml, pwd, c_id, card) são mantidos por contrato e mapeados no controller (PB-12).

### F17 [LOW] Código e configuração mortos (AP-20)
File: src/utils.js:2-3, 5, 10, 25
File: src/AppManager.js:2, 104
Description: config.dbUser, dbPass e smtpUser nunca são lidos. totalRevenue é exportado e importado em AppManager.js:2 sem uso. A coluna `email` é selecionada em :104 e descartada. Routes: nenhuma
Impact: ruído e falsa impressão de que existem banco com credencial e SMTP.
Recommendation: remover os itens não usados (PB-14).

### F18 [LOW] console.log como logging (AP-21)
File: src/utils.js:13
File: src/AppManager.js:45
File: src/app.js:13
Description: eventos de aplicação registrados com console.log, sem nível nem estrutura. Routes: nenhuma
Impact: impossível filtrar por severidade ou silenciar em produção.
Recommendation: módulo src/utils/logger.js com níveis (info/warn/error) controlados por LOG_LEVEL (PB-14).

### F19 [LOW] API de callbacks do sqlite3 (padrão legado) (AP-22)
File: src/AppManager.js:11-21, 37, 40, 50, 54, 57, 83, 92, 104, 106, 133
Description: todo o acesso ao banco usa a API somente-callback do sqlite3 (db.run/get/all com callback), em vez de Promises/async-await. Routes: nenhuma
Impact: induz o callback hell de F09 e impede o uso de try/catch.
Recommendation: wrapper com Promises (new Promise sobre run/get/all) e async/await em todas as camadas (PB-11).

## Deprecated APIs
| API usada | Local | Versão detectada | Substituir por |
|---|---|---|---|
| sqlite3 API somente-callback (db.run/get/all) | src/AppManager.js:11-21, 37-133 | sqlite3 5.1.7 / Node 22 | wrapper com Promises + async/await |
Nenhuma API removida do Express 4→5 (req.param, res.send(status), app.del, body-parser) nem do Node (new Buffer, url.parse, fs.exists etc.) foi encontrada.

## Architecture verdict
Current: Monolítica / sem camadas
Target:  MVC — desmontar AppManager em config, database, models, services, controllers, routes e middlewares, com app.js como composition root e dependências injetadas.

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
