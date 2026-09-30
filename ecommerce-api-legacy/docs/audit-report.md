```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2 (resolved 4.22.1)
Files:   3 analyzed | ~180 lines of code
Date:    2026-09-30

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 5

## Findings

### F01 [CRITICAL] Hardcoded Credentials (AP-01)
File: src/utils.js:1-7
Description: o objeto exportado `config` contém literais `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (prefixo de chave de produção) e `smtpUser`, além da porta fixa.
Impact: qualquer pessoa com acesso ao repositório obtém a senha do banco e a chave do gateway de pagamento; rotacionar exige commit e deploy.
Recommendation: mover para `src/config` lendo `process.env` (com `.env.example` sem valores reais) e remover as chaves não usadas (PB-01).

### F02 [CRITICAL] Card number and gateway key written to logs (AP-06)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão (PAN) e a chave secreta do gateway no stdout a cada checkout.
Impact: violação de PCI-DSS/LGPD; quem lê os logs obtém cartões e a chave de produção.
Recommendation: não logar PAN nem segredos; no máximo mascarar os últimos 4 dígitos, usando um logger central (PB-06).

### F03 [CRITICAL] Weak password hashing and default password (AP-04)
File: src/utils.js:17-23
File: src/AppManager.js:18, 68
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres. É determinístico, sem salt e reversível na prática: senhas com o mesmo prefixo geram o mesmo "hash". O checkout usa `badCrypto(p || "123456")`, criando a conta com senha padrão quando `pwd` não vem. O seed grava `'123'` em texto puro.
Impact: um vazamento do banco expõe as senhas; contas criadas sem senha ficam acessíveis com "123456".
Recommendation: usar `crypto.scrypt` com salt aleatório (stdlib), exigir `pwd` e gravar o seed já com hash (PB-06).

### F04 [CRITICAL] Administrative/destructive endpoints without authentication (AP-05)
File: src/AppManager.js:80, 131-137
Description: `GET /api/admin/financial-report` devolve receita e nomes de alunos, e `DELETE /api/users/:id` apaga usuários. Nenhuma das duas tem middleware de autenticação ou autorização, e não existe mecanismo de auth no projeto.
Impact: qualquer cliente anônimo lê dados financeiros e pessoais e apaga contas.
Recommendation: proteger as rotas admin com middleware de autenticação (ex.: token de admin via env, header `Authorization`) (PB-13).

### F05 [CRITICAL] God Class AppManager (AP-03)
File: src/AppManager.js:4-139
Description: a mesma classe instancia o banco (:7), cria o schema e o seed (:10-23), registra as 3 rotas (:25-138) e implementa a regra de pagamento, matrícula, auditoria e relatório com SQL inline. O handler de checkout tem 51 linhas e o de relatório tem 50.
Impact: impossível testar regra de negócio ou dados isoladamente; qualquer mudança toca o arquivo inteiro.
Recommendation: separar em config / database / models (repositórios) / services / controllers / routes, com composition root em app.js (PB-03).

### F06 [HIGH] Business rules inside route handlers (AP-07)
File: src/AppManager.js:28-78, 80-129
Description: o handler de checkout decide a aprovação do pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`, :46), cria usuário, matrícula, pagamento e auditoria. O handler do relatório calcula a receita (`courseData.revenue += payment.amount`, :108-110) e monta a agregação.
Impact: regras de pagamento e receita só são testáveis via HTTP e não podem ser reutilizadas.
Recommendation: extrair CheckoutService/ReportService e deixar controllers finos (PB-04).

### F07 [HIGH] Callback hell with manual pending counters (AP-11)
File: src/AppManager.js:26, 37-77, 83-128
Description: o checkout encadeia 6 níveis de callbacks (course → user → enrollments → payments → audit_logs) e usa `const self = this` para escapar de `function(err)`. O relatório usa os contadores `coursesPending--` / `enrPending--` (:86-121) para saber quando responder.
Impact: erros não propagam, respostas podem nunca ser enviadas ou sair duplicadas, e o código fica ilegível.
Recommendation: promisificar o driver (wrapper async sobre sqlite3) e reescrever com async/await (PB-08).

### F08 [HIGH] Mutable global state (AP-08)
File: src/utils.js:9-15, 25
Description: `let globalCache = {}` é mutado por `logAndCache` a cada checkout (`last_checkout_${userId}`) e exportado junto com `let totalRevenue = 0`. O cache cresce sem limite e nunca é lido.
Impact: vazamento de memória, estado compartilhado entre requisições e impossibilidade de escalar horizontalmente.
Recommendation: remover o cache global. Se for necessário, usar um componente injetado com escopo definido (PB-05).

### F09 [HIGH] Tight coupling to concrete infrastructure (AP-09)
File: src/AppManager.js:1, 7
File: src/app.js:8-10
Description: `AppManager` faz `new sqlite3.Database(':memory:')` no construtor e importa `config` e os utilitários diretamente. `app.js` depende da classe concreta para inicializar o banco e as rotas.
Impact: não é possível injetar outro banco ou fakes em testes, e trocar a infraestrutura exige alterar a regra de negócio.
Recommendation: criar a conexão no composition root e injetá-la em repositórios, services e controllers (PB-05).

### F10 [MEDIUM] N+1 queries in financial report (AP-13)
File: src/AppManager.js:83, 89-106
Description: 1 query de courses, mais 1 de enrollments por curso (:92), mais 2 por matrícula (users :104, payments :106). O total é 1 + C + 2E queries.
Impact: a latência cresce linearmente com o número de matrículas.
Recommendation: uma única query com `LEFT JOIN` courses/enrollments/users/payments, agregada em memória no service (PB-07).

### F11 [MEDIUM] Multi-step writes without transaction / orphaned rows (AP-14)
File: src/AppManager.js:12-16, 50-61, 69, 133-135
Description: o checkout grava users, enrollments, payments e audit_logs em sequência, sem BEGIN/COMMIT/ROLLBACK. Uma falha no meio deixa a matrícula sem pagamento. `DELETE FROM users` não trata enrollments/payments (a própria resposta admite "ficaram sujos no banco"). O schema não declara FOREIGN KEYs.
Impact: dados inconsistentes e relatório com alunos "Unknown".
Recommendation: envolver o checkout em transação e tratar os dependentes no delete, também dentro de transação (PB-10).

### F12 [MEDIUM] Weak input validation (AP-16)
File: src/AppManager.js:29-35, 46, 132
Description: o checkout só verifica presença (`if (!u || !e || !cid || !cc)`). `pwd` é opcional, email e card não têm formato validado e `c_id` não tem tipo validado. Se `card` vier como número, `cc.startsWith` lança TypeError dentro do callback do sqlite e derruba o processo. `:id` do DELETE também não é validado.
Impact: um único request malformado pode derrubar a API, e dados inválidos entram no banco.
Recommendation: validar tipos e formatos no controller/validator antes de chamar o service (PB-12).

### F13 [MEDIUM] Swallowed errors and no central error handler (AP-17)
File: src/AppManager.js:57, 92-93, 104-106, 133-135
Description: o callback do audit_logs ignora `err`. Em :92, com `err`, `enrollments.length` lança TypeError e derruba o processo. Em :104/:106, `err` é ignorado. O DELETE responde sucesso mesmo com erro ou id inexistente. Os erros saem como texto solto em formatos variados, e não há middleware `(err, req, res, next)`.
Impact: crashes do processo, falhas silenciosas e respostas enganosas.
Recommendation: propagar erros via async/await até um error middleware central (PB-09).

### F14 [LOW] Magic numbers / strings (AP-18)
File: src/AppManager.js:18-21, 46, 68, 108
File: src/utils.js:6, 19-22
Description: os status `"PAID"`/`"DENIED"` aparecem como strings soltas. Também há o prefixo `"4"` como regra de aprovação, a senha padrão `"123456"`, as constantes `10000`, `2` e `10` do hash e a porta `3000`.
Impact: regras de negócio ficam implícitas e são fáceis de divergir.
Recommendation: constantes nomeadas (ex.: `PaymentStatus`) e porta via config (PB-12).

### F15 [LOW] Poor naming (AP-19)
File: src/AppManager.js:4, 29-33
File: src/utils.js:17
Description: as variáveis `u, e, p, cid, cc` têm nomes sem significado. A classe `AppManager` e o módulo `utils` têm nomes genéricos, e `badCrypto` tem um nome enganoso. Os campos da API (`usr`, `eml`, `pwd`, `c_id`, `card`) são abreviados.
Impact: leitura e manutenção difíceis.
Recommendation: renomear internamente (name, email, password, courseId, cardNumber), mapeando as chaves do contrato no controller, que continuam iguais (PB-12).

### F16 [LOW] Dead code and unused exports (AP-20)
File: src/AppManager.js:2, 104
File: src/utils.js:2-3, 5, 10, 25
Description: `totalRevenue` é importado e nunca usado. `globalCache` é gravado e nunca lido. `config.dbUser`, `dbPass` e `smtpUser` nunca são referenciados. A query de :104 seleciona `email` sem usá-lo.
Impact: ruído e falsa impressão de funcionalidade.
Recommendation: remover (PB-14).

### F17 [LOW] console.log as logging (AP-21)
File: src/app.js:13
File: src/utils.js:13
File: src/AppManager.js:45
Description: eventos e "cache" são registrados com `console.log`, sem níveis.
Impact: não é possível filtrar ou desligar logs por ambiente, e há risco de vazamento (ver F02).
Recommendation: logger mínimo com níveis em um módulo próprio (PB-14).

### F18 [LOW] Callback-only sqlite3 API usage (AP-22)
File: src/AppManager.js:37-135
Description: todo o acesso a dados usa a API de callbacks do `sqlite3` (`db.get/all/run(sql, params, cb)`), mesmo com Node 22 oferecendo `util.promisify` e async/await.
Impact: é a causa raiz de F07 e F13.
Recommendation: wrapper baseado em Promise sobre o driver (PB-11, PB-08).

## Deprecated APIs
| API usada | Local | Versão detectada | Substituir por |
|---|---|---|---|
| sqlite3 com callbacks aninhados (padrão legado) | src/AppManager.js:37-135 | sqlite3 5.1.7 / Node 22 | wrapper com Promise (`util.promisify` / async-await) |
Nenhuma API removida no Express 4 → 5 foi encontrada (`req.param`, `res.send(status)`, `app.del`, `body-parser`: 0 ocorrências). `Buffer.from` (utils.js:19) já é a forma moderna.

## Architecture verdict
Current: Monolítica / sem camadas (God Class AppManager com banco + seed + rotas + regra)
Target:  MVC — desmontar AppManager em config, database, models (repositórios), services, controllers e routes, com app.js como composition root e error middleware central.

================================
Total: 18 findings
================================
```
