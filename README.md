# Refactor-Arch — Skill de Refatoração Arquitetural Automatizada

Entrega do desafio **"Criação de Skills — Refatoração Arquitetural Automatizada"** do MBA em Engenharia de Software com IA.
O enunciado original está no [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).

A skill `refactor-arch` (Claude Code) analisa uma codebase, audita anti-patterns por severidade e refatora o projeto para o padrão **MVC**. Ela foi validada em três projetos legados:

| # | Projeto | Stack | Domínio |
|---|---------|-------|---------|
| 1 | `code-smells-project/` | Python + Flask 3.1 + sqlite3 | API de E-commerce (produtos, usuários, pedidos) |
| 2 | `ecommerce-api-legacy/` | Node.js + Express 4 + sqlite3 | LMS com fluxo de checkout (cursos, matrículas, pagamentos) |
| 3 | `task-manager-api/` | Python + Flask 3.0 + SQLAlchemy | Task Manager (tasks, usuários, categorias, relatórios) |

---

## A) Análise Manual

Antes de escrever a skill, li o código dos três projetos linha a linha para entender **quais padrões ela precisa detectar**. A classificação segue a escala do desafio:

- **CRITICAL:** segurança ou quebra total da separação de responsabilidades.
- **HIGH:** violação forte de MVC/SOLID.
- **MEDIUM:** duplicação, performance e validação.
- **LOW:** legibilidade.

### Projeto 1 — `code-smells-project` (Python/Flask)

**Arquitetura atual:** monolito em 4 arquivos. `app.py` mistura configuração, rotas e endpoints administrativos. `controllers.py` concentra validação, regra de negócio e notificações. `models.py` concentra o SQL dos 4 domínios. Não existem camadas de config, service nem error handling.

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | **SQL Injection:** queries montadas por concatenação de strings com dados vindos do request | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 149-166, 280, 289-297` | Um payload como `' OR '1'='1` no `/login` autentica sem senha. Qualquer campo de texto permite ler ou destruir o banco. |
| CRITICAL | **Credenciais hardcoded e vazadas:** `SECRET_KEY` fixa no código, que ainda é devolvida pelo `/health` | `app.py:7`; `controllers.py:285-289` | Quem lê o repositório ou chama `/health` obtém a chave usada para assinar sessões. |
| CRITICAL | **Endpoints administrativos sem autenticação:** `/admin/query` executa SQL arbitrário e `/admin/reset-db` apaga todas as tabelas | `app.py:47-78` | Qualquer cliente anônimo controla o banco inteiro (RCE de dados). |
| CRITICAL | **Senhas em texto puro e expostas:** o seed grava senhas sem hash e `GET /usuarios` devolve o campo `senha` | `database.py:75-83`; `models.py:83, 99` | Um vazamento do banco ou uma única chamada ao endpoint expõe as senhas de todos os usuários. |
| HIGH | **God file / mistura de camadas:** `models.py` reúne acesso a dados, regra de negócio (faixas de desconto) e formatação de 4 domínios | `models.py:1-314` (desconto em `256-262`) | Não dá para testar a regra de desconto sem banco, e qualquer mudança mexe em tudo. |
| HIGH | **Estado global mutável:** uma conexão SQLite global compartilhada entre threads (`check_same_thread=False`) | `database.py:4-10` | Causa acoplamento implícito, impede injeção de dependência e traz risco de condições de corrida. |
| HIGH | **Efeitos colaterais no controller:** "envio" de e-mail, SMS e push feito com `print` dentro do controller | `controllers.py:208-210, 247-250` | Mistura responsabilidades. Deveria ser um serviço de notificação injetável. |
| HIGH | **Debug ligado em "produção":** `DEBUG=True` e `debug=True` com `host=0.0.0.0` | `app.py:8, 88` | O debugger do Werkzeug permite execução remota de código quando exposto na rede. |
| MEDIUM | **Queries N+1:** cada pedido faz uma query de itens, e cada item faz outra de produto | `models.py:171-201, 203-233` | Com P pedidos e I itens são 1 + P + P·I queries. Degrada rápido com volume. |
| MEDIUM | **Validação duplicada:** as mesmas regras de produto repetidas em criar e atualizar, e `atualizar` ainda pula parte delas | `controllers.py:24-62` vs `64-96` | Regras divergem com o tempo. Hoje dá para atualizar um produto com categoria inválida ou nome vazio. |
| MEDIUM | **Pedido sem transação:** o estoque é validado e depois decrementado em passos separados, sem rollback em caso de erro | `models.py:133-169` | Uma falha no meio deixa o pedido criado sem itens ou o estoque inconsistente. |
| MEDIUM | **Tratamento de erro repetido e vazando detalhes:** `try/except Exception` em todo controller devolvendo `str(e)` | `controllers.py` (todas as funções) | O código se repete e expõe detalhes internos (SQL, stack) ao cliente. Pede um error handler central. |
| LOW | **`print` como logging** | `controllers.py:8, 57, 106, 161, 179, 182, 219`; `app.py:56, 83-86` | Sem nível, sem formato e impossível de desligar ou redirecionar. |
| LOW | **Magic numbers e listas soltas:** `10000/5000/1000`, `0.1/0.05/0.02`, lista de categorias e de status inline | `models.py:257-262`; `controllers.py:52, 242` | A regra de negócio fica escondida e difícil de alterar. |
| LOW | **Imports não usados e nomes ruins:** `import sqlite3`, `request` em `app.py`, parâmetro `id` sombreando o builtin, `cursor2/cursor3` | `models.py:2`; `app.py:1`; `models.py:24, 187, 191` | Ruído que dificulta a leitura. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express)

**Arquitetura atual:** a classe `AppManager` é uma *God Class*: cria o banco em memória, faz o seed, registra as rotas e executa toda a regra de negócio dentro dos handlers. `utils.js` mistura config, cache global e "criptografia".

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Credenciais hardcoded:** usuário/senha de banco, chave *live* do gateway de pagamento e usuário SMTP no código | `src/utils.js:1-7` | Segredos de produção versionados. Quem tem acesso ao repositório tem acesso ao gateway. |
| CRITICAL | **Dado de cartão logado:** o número completo do cartão e a chave do gateway vão para o `console.log` | `src/AppManager.js:45` | Viola PCI-DSS. Os logs passam a conter PAN. |
| CRITICAL | **God Class:** `AppManager` concentra schema, seed, rotas, checkout, relatório e deleção | `src/AppManager.js:1-141` | Não há separação alguma entre Model, View e Controller. É impossível testar ou reutilizar partes isoladas. |
| CRITICAL | **Hash de senha inseguro:** `badCrypto` é um base64 truncado e repetido, reversível e sem salt, com senha padrão `"123456"` | `src/utils.js:17-23`; `src/AppManager.js:68` | As senhas ficam praticamente em texto puro. |
| HIGH | **Callback hell com regra de negócio na rota:** o checkout (buscar curso → usuário → pagamento → matrícula → auditoria) fica aninhado em 5 níveis dentro do handler | `src/AppManager.js:28-78` | Ilegível e sem ponto único de tratamento de erro. A lógica de pagamento está presa à camada HTTP. |
| HIGH | **Estado global mutável:** `globalCache` e `totalRevenue` exportados como variáveis de módulo | `src/utils.js:9-15, 25` | Estado compartilhado e escondido. Vaza memória (o cache nunca é limpo) e quebra com múltiplas instâncias. |
| HIGH | **Endpoints sensíveis sem autenticação:** relatório financeiro e deleção de usuário abertos | `src/AppManager.js:80, 131` | Qualquer cliente lê o faturamento ou apaga usuários. |
| MEDIUM | **Queries N+1 no relatório financeiro:** para cada curso busca as matrículas, e para cada matrícula busca usuário e pagamento | `src/AppManager.js:83-128` | São 1 + C + 2·M queries, quando um único `JOIN` resolveria. |
| MEDIUM | **Sem transação / integridade:** o checkout grava matrícula, pagamento e log em passos independentes, e o DELETE de usuário deixa matrículas e pagamentos órfãos (a própria resposta admite) | `src/AppManager.js:50-61, 131-137` | O banco fica inconsistente em qualquer falha parcial. |
| MEDIUM | **Erros ignorados:** callbacks descartam `err` e o relatório quebra com `enrollments.length` se `err` vier preenchido | `src/AppManager.js:57, 92-93, 104, 106, 133` | Falhas silenciosas ou crash do processo. |
| MEDIUM | **Validação fraca de entrada:** só checa presença, sem validar formato de e-mail, cartão ou tipo do `c_id` | `src/AppManager.js:35` | Dados inválidos chegam ao banco e ao "gateway". |
| LOW | **Nomes crípticos no payload e no código:** `usr`, `eml`, `pwd`, `c_id`, `card`, `u`, `e`, `p`, `cid`, `cc` | `src/AppManager.js:29-33` | Leitura difícil e contrato de API pouco autoexplicativo. |
| LOW | **Magic values:** cartão aprovado se começar com `"4"`, porta `3000`, status `"PAID"/"DENIED"` como strings soltas | `src/AppManager.js:46`; `src/utils.js:6` | A regra de negócio fica implícita. |
| LOW | **Código morto e estilo:** `totalRevenue` nunca usado, `let` onde caberia `const`, `const self = this` misturado com arrow functions | `src/utils.js:10`; `src/AppManager.js:26, 29-33` | Ruído e inconsistência. |

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy)

**Arquitetura atual:** já tem pastas `models/`, `routes/`, `services/` e `utils/`, mas **não há controllers**. As rotas fazem validação, regra de negócio, consultas e serialização. `helpers.py` tem utilitários e constantes que ninguém usa, e o `NotificationService` também não é usado.

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Credenciais hardcoded:** `SECRET_KEY` e usuário/senha SMTP no código | `app.py:13`; `services/notification_service.py:6-10` | Segredos versionados, como nos outros projetos. |
| CRITICAL | **Hash de senha fraco (MD5 sem salt)** | `models/user.py:27-32` | MD5 é quebrado por rainbow tables em segundos. |
| CRITICAL | **Hash da senha exposto na API:** `User.to_dict()` inclui `password`, usado no login, no cadastro, no update e no GET de usuário | `models/user.py:21`; `routes/user_routes.py:33, 85, 129, 209` | Qualquer consulta de usuário entrega o hash, que por ser MD5 é praticamente a senha. |
| HIGH | **Autenticação falsa:** o login devolve `'fake-jwt-token-<id>'` previsível e nenhuma rota verifica token | `routes/user_routes.py:210` | Qualquer um forja um token. Na prática não existe controle de acesso. |
| HIGH | **Ausência de camada Controller/Service:** rotas com 50-100 linhas de regra de negócio (relatórios, validação, agregações) | `routes/report_routes.py:12-155`; `routes/task_routes.py:85-223` | Viola SRP. A regra de negócio só é testável via HTTP. |
| HIGH | **Debug ligado:** `debug=True` com `host=0.0.0.0` | `app.py:34` | Mesmo risco de RCE via debugger do Werkzeug. |
| MEDIUM | **Queries N+1:** `User.query.get` e `Category.query.get` dentro do loop de tasks, contagem por usuário e por categoria em loop, e `len(u.tasks)` com lazy load | `routes/task_routes.py:41-57`; `routes/report_routes.py:55-68, 161-163`; `routes/user_routes.py:22` | Com N tasks são 2N+1 queries só para listar. |
| MEDIUM | **Lógica duplicada:** o cálculo de "overdue" aparece 7 vezes, e a validação de task é repetida em create/update enquanto `process_task_data` e `VALID_STATUSES` em `helpers.py` não são usados | `models/task.py:50-60`; `routes/task_routes.py:30-39, 71-80, 283-287`; `routes/report_routes.py:33-43, 132-135`; `routes/user_routes.py:171-180`; `utils/helpers.py:57-116` | Qualquer mudança de regra precisa ser feita em 7 lugares. |
| MEDIUM | **`except:` sem tipo engolindo erros** | `routes/task_routes.py:62, 137, 204, 236`; `routes/report_routes.py:186, 207, 221`; `routes/user_routes.py:130, 149`; `utils/helpers.py:46, 49, 88` | Captura até `KeyboardInterrupt`/`SystemExit` e esconde a causa raiz. |
| MEDIUM | **Validação ausente:** `priority` não é checada quanto ao tipo (`"alta" < 1` gera `TypeError` → 500) e `int(priority)` na busca não é tratado | `routes/task_routes.py:113, 182, 261, 264` | O cliente consegue derrubar o endpoint com 500 em vez de receber 400. |
| LOW | **APIs deprecated:** `Model.query.get()` é legado no SQLAlchemy 2.x (use `db.session.get(Model, id)`) e `datetime.utcnow()` está deprecated desde o Python 3.12 (use `datetime.now(timezone.utc)`) | 16 ocorrências de `.query.get(` em `routes/*.py`; 22 ocorrências de `utcnow` (ex.: `models/task.py:15-16, 52`, `routes/task_routes.py:31, 215`) | Geram `DeprecationWarning` hoje e vão quebrar em versões futuras. |
| LOW | **Imports não usados:** `os, sys, json` e afins | `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:8`; `utils/helpers.py:3-7` | Ruído. |
| LOW | **Booleanos verbosos e magic numbers:** `if x: return True else: return False`, prioridades `1..5` e `<= 2`, tamanho mínimo de senha `4` | `models/task.py:38-48`; `models/user.py:34-38`; `routes/report_routes.py:129`; `routes/user_routes.py:64` | Legibilidade. As constantes já existem em `helpers.py`, mas não são usadas. |

### O que essa análise ensinou para a skill

Os três projetos compartilham **os mesmos tipos de problema em formas diferentes**. A skill precisa detectar conceitos, não sintaxe específica:

1. **Segredos no código:** string literal atribuída a chaves como `SECRET`, `PASS`, `KEY`, `TOKEN`.
2. **SQL Injection:** concatenação ou interpolação de strings dentro de `execute`/`run`/`query`.
3. **Consulta dentro de loop (N+1):** `for`/`forEach` contendo chamada ao banco ou ORM.
4. **Regra de negócio na camada HTTP:** handler de rota com cálculos, agregações ou múltiplas queries.
5. **Hash fraco / senha exposta:** `md5`, `sha1`, base64 e serialização incluindo o campo de senha.
6. **Estado global mutável:** variáveis de módulo reatribuídas ou mutadas.
7. **APIs deprecated:** específicas de cada ecossistema (`Query.get`, `utcnow`, callbacks vs. `async/await`).

Um ponto importante: o **projeto 3 já "parece" organizado**, mas tem os mesmos problemas de fundo. A skill precisa avaliar **responsabilidades**, e não apenas a existência de pastas.

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestrador: regras invioláveis + 3 fases
└── references/
    ├── project-analysis.md               # Fase 1 — heurísticas de detecção de stack/arquitetura
    ├── anti-patterns-catalog.md          # Fase 2 — 22 anti-patterns + APIs deprecated
    ├── audit-report-template.md          # Fase 2 — formato do relatório
    ├── mvc-guidelines.md                 # Fase 3 — arquitetura-alvo e regras de contrato
    └── refactoring-playbook.md           # Fase 3 — 14 transformações antes/depois
```

| Área de conhecimento exigida | Arquivo |
|---|---|
| Análise de projeto | `project-analysis.md` |
| Catálogo de anti-patterns | `anti-patterns-catalog.md` |
| Template de relatório | `audit-report-template.md` |
| Guidelines de arquitetura | `mvc-guidelines.md` |
| Playbook de refatoração | `refactoring-playbook.md` |

### Decisões de design

1. **O SKILL.md diz *o quê* e *quando*; as referências dizem *como*.** O SKILL.md tem menos de 100 linhas e manda ler cada referência **só no início da fase que a usa** (*progressive disclosure*). O agente não gasta contexto com o playbook enquanto audita, e o SKILL.md fica abaixo do limite recomendado pela documentação (~5k tokens).
2. **Regras invioláveis no topo do SKILL.md.** São elas:
   - Fases 1 e 2 são somente leitura.
   - Todo finding cita `arquivo:linha` conferido no código.
   - O contrato da API e o comando de start são preservados.
   - A skill não mexe no índice do git.
   - A refatoração se adapta ao nível de organização do projeto.
3. **Pausa obrigatória com pergunta fixa.** A Fase 2 termina com `Proceed with refactoring (Phase 3)? [y/n]` e a instrução explícita de **não chamar nenhuma ferramenta de escrita** até a resposta.
4. **Validação por baseline.** Antes de alterar qualquer coisa, a Fase 3 sobe a aplicação original e registra status e chaves JSON de cada endpoint. Depois da refatoração, repete as mesmas requisições e compara. Assim "os endpoints continuam funcionando" vira uma verificação objetiva, e não uma impressão do modelo.
5. **Mudanças de contrato só por segurança, e sempre documentadas.** As guidelines (§6) listam o que pode mudar: remover campos sensíveis, proteger rotas admin, trocar 500 por 400 em entrada inválida. Cada execução gera `docs/refactor-summary.md` com a seção *Intentional contract changes*.
6. **IDs cruzados.** O finding `F01` aponta o anti-pattern `AP-02`, que aponta o padrão `PB-02`. Com isso o relatório, o catálogo e o playbook formam uma cadeia rastreável.
7. **Sem `disable-model-invocation`.** A skill começou com essa opção, mas ela escondia a skill do menu (ver Desafios). A segurança fica garantida pela pausa da Fase 2.

### Anti-patterns do catálogo (22)

| Severidade | Anti-patterns | Por que entraram |
|---|---|---|
| CRITICAL (6) | AP-01 Segredos hardcoded · AP-02 SQL Injection · AP-03 God Class/File · AP-04 Senha em texto puro/hash fraco · AP-05 Endpoint admin sem auth · AP-06 Exposição de dados sensíveis | Apareceram na análise manual em pelo menos 2 dos 3 projetos e têm impacto direto em segurança ou na separação de camadas |
| HIGH (6) | AP-07 Regra de negócio na rota · AP-08 Estado global mutável · AP-09 Acoplamento sem DI · AP-10 Debug/CORS inseguro · AP-11 Callback hell · AP-12 Autenticação falsa | Violações de MVC/SOLID que impedem testes. AP-11 cobre a variante assíncrona do Node |
| MEDIUM (5) | AP-13 N+1 · AP-14 Sem transação/integridade · AP-15 Duplicação · AP-16 Validação fraca · AP-17 Erros engolidos/espalhados | Performance e consistência de dados, todos presentes nos 3 projetos |
| LOW (5) | AP-18 Magic numbers · AP-19 Nomes ruins · AP-20 Código morto · AP-21 print/console.log · AP-22 **APIs deprecated** | Legibilidade. AP-22 tem uma tabela por ecossistema (Python, SQLAlchemy, Flask, Werkzeug, Node, Express, Java, PHP) com o equivalente moderno |

Cada entrada tem **sinais de detecção acionáveis** (regex para `grep -nE`), **falsos positivos** a descartar, impacto e o padrão de correção. O playbook tem **14 padrões** (PB-01…PB-14) com código antes/depois em Python e JavaScript.

### Como a skill é agnóstica de tecnologia

- **Detecção por conceito, não por sintaxe.** Estado global mutável aparece como `global db_connection` em Python e como `let globalCache = {}` em JS, e os dois casos estão descritos no mesmo anti-pattern.
- **A Fase 1 descobre a stack pelos manifestos.** A tabela cobre `requirements.txt`, `package.json`, `pom.xml`, `go.mod`, `composer.json`, `Gemfile` e `*.csproj`. Depois confirma pelos imports.
- **As guidelines definem a mesma arquitetura com estruturas por stack.** Há estruturas para Flask monolítico, Flask parcialmente organizado e Express, além de mapeamentos para Django, FastAPI e Spring.
- **Nenhuma referência a nomes dos projetos-alvo** no SKILL.md. Os exemplos do playbook ilustram padrões, não arquivos específicos.
- **Prova prática:** a **mesma cópia** da skill (verificada com `diff -r`) rodou nos 3 projetos, em duas linguagens e dois níveis de organização.

### Desafios encontrados e como resolvi

| # | Desafio | Solução |
|---|---|---|
| 1 | **O regex de segredos não pegava casos reais.** A primeira versão não detectava `app.config["SECRET_KEY"] = "..."` (por causa do `"]` antes do `=`) nem `paymentGatewayKey` (camelCase). | Testei os regex contra os 3 projetos **antes** do commit e reescrevi o padrão para `(secret\|pass\|key\|token\|senha\|chave)\w*["']?\]?\s*[:=]\s*["'][^"']{4,}["']`, que pega os 7 casos. |
| 2 | **A skill não aparecia no `/refactor`.** | Duas causas. (a) `disable-model-invocation: true` esconde a skill do menu, e eu removi a opção. (b) O Claude estava sendo aberto na **raiz** do repositório: skills em subpastas (`code-smells-project/.claude/skills`) só carregam quando o Claude é aberto dentro delas ou quando mexe em arquivos dali. Diagnostiquei com `claude -p "liste as skills"` rodado dentro do projeto. |
| 3 | **A skill usou `git rm` no projeto 1.** As remoções ficaram no *staging* e entraram por engano no commit do relatório. | Refiz os commits com `git reset --soft` (ainda locais) e acrescentei a **regra 6** ao SKILL.md: nada de `git add/rm/mv/commit`. Nos projetos 2 e 3 as mudanças ficaram fora do staging, como esperado. |
| 4 | **Senha com hash quebra o banco antigo.** Trocar texto puro/MD5 por hash seguro faz o login falhar com o `.db` gerado antes. | O playbook (PB-06) e o SKILL.md instruem apagar os bancos locais gerados pelo baseline e rodar o seed de novo. |
| 5 | **`utcnow()` → `datetime.now(timezone.utc)` gera `TypeError`** ao comparar com datas *naive* do SQLite. | O PB-11 traz um helper `utcnow()` que devolve UTC *naive*. A skill aplicou esse helper no projeto 3, validado com `python -W error::DeprecationWarning seed.py`. |
| 6 | **Quanto do contrato mudar?** Proteger todas as rotas quebraria os clientes. | Regra §6 das guidelines: só rotas administrativas/destrutivas globais ganham auth. No projeto 3 a skill também protegeu `DELETE /users/<id>`, que apaga o usuário e todas as suas tasks (finding CRITICAL). É uma exceção à regra 6.5, mas a skill justificou e documentou. |

---

## C) Resultados

### Findings por severidade

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | 6 | 5 | 5 | 5 | **21** | [audit-project-1.md](reports/audit-project-1.md) |
| 2 — ecommerce-api-legacy | 5 | 4 | 4 | 5 | **18** | [audit-project-2.md](reports/audit-project-2.md) |
| 3 — task-manager-api | 4 | 4 | 5 | 5 | **18** | [audit-project-3.md](reports/audit-project-3.md) |

Nos 3 projetos, os findings da skill incluem **todos** os problemas da análise manual (seção A). A skill ainda achou problemas que eu não tinha listado:

- **P1:** `deletar_produto` deixava itens órfãos e o cancelamento de pedido não devolvia o estoque.
- **P2:** um `card` numérico derrubava o processo (TypeError dentro do callback do sqlite).
- **P3:** `POST /users` permitia escalar privilégio com `"role": "admin"`.

### Estrutura antes → depois

**Projeto 1 — monolito → `src/` com camadas**
```
ANTES                         DEPOIS
app.py                        app.py                       (lançador: python app.py)
controllers.py                src/app.py                   (create_app)
models.py                     src/config/{settings,constants}.py
database.py                   src/database/connection.py   (conexão por request em flask.g)
requirements.txt              src/models/{produto,usuario,pedido,relatorio,admin}_model.py
                              src/controllers/{produto,usuario,pedido,relatorio,admin,health}_controller.py
                              src/views/{produto,usuario,pedido,relatorio,admin,health}_routes.py
                              src/services/notification_service.py
                              src/middlewares/{error_handler,auth}.py
                              src/errors.py · .env.example · docs/
```

**Projeto 2 — God Class → camadas com injeção de dependência**
```
ANTES                         DEPOIS
src/app.js                    src/app.js                   (composition root, npm start)
src/AppManager.js             src/config/{index,constants}.js
src/utils.js                  src/database/{connection,schema}.js   (wrapper Promise + transaction)
                              src/models/{user,course,enrollment,payment,auditLog}Model.js
                              src/controllers/{checkout,report,user}Controller.js
                              src/routes/{checkout,admin,user}Routes.js
                              src/services/paymentService.js
                              src/middlewares/{asyncHandler,auth,errorHandler}.js
                              src/utils/{logger,password}.js · src/errors.js · .env.example · docs/
```

**Projeto 3 — camadas parciais → camadas completas (sem mover tudo)**
```
ANTES                         DEPOIS
app.py                        app.py                       (create_app, python app.py)
database.py                   database.py
seed.py                       seed.py
models/{task,user,category}   models/{task,user,category,base}.py
routes/{task,user,report}     routes/{task,user,report,category,system}_routes.py   (View)
services/notification         services/{notification,token}_service.py
utils/helpers.py              utils/helpers.py             (validadores e helper utcnow usados de fato)
                              config/{settings,constants}.py              ← novo
                              controllers/{task,user,report,category}_controller.py  ← novo
                              middlewares/{error_handler,auth}.py         ← novo
                              .env.example · docs/
```

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript (Node) | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.18.2 (4.22.1 instalado) | ✅ Flask 3.0.0 + SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Nº de arquivos condiz | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Findings com arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 21 | ✅ 18 | ✅ 18 |
| APIs deprecated verificadas | ✅ nenhuma (correto para Flask 3.1) | ✅ callbacks do sqlite3 (padrão legado) | ✅ `Query.get()`, `datetime.utcnow()` |
| Pausa e pede confirmação | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ | ✅ | ✅ |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `src/views/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `app.py` → `create_app()` | ✅ `src/app.js` | ✅ `app.py` → `create_app()` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ (sem warnings de deprecated) |
| Endpoints originais respondem | ✅ 19/19 rotas | ✅ 3/3 rotas | ✅ 22/22 rotas |

### Logs das aplicações rodando após a refatoração

Minha validação foi independente da skill: apaguei o banco, subi o app com o comando de start original e chamei cada rota com `curl`.

**Projeto 1** — `ADMIN_TOKEN=tok123 python app.py`
```
SECRET_KEY não definida; usando valor aleatório (apenas desenvolvimento)
INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Debug mode: off
GET     /                                -> 200
GET     /health                          -> 200  {"ambiente":"development","counts":{...},"status":"ok"}   (sem secret_key)
GET     /produtos                        -> 200
GET     /produtos/busca?q=Mouse&preco_min=10 -> 200
GET     /produtos/999                    -> 404  {"erro":"Produto não encontrado","sucesso":false}
POST    /produtos                        -> 201
POST    /produtos  (preco "abc")         -> 400  {"erro":"Preço deve ser numérico"}      (antes: 500)
PUT     /produtos/11                     -> 200
GET     /usuarios                        -> 200  (sem campo senha)
POST    /usuarios                        -> 201
POST    /login                           -> 200
POST    /login  (' OR '1'='1)            -> 401  (SQL Injection bloqueada)
POST    /pedidos                         -> 201
GET     /pedidos · /pedidos/usuario/2    -> 200 · 200
PUT     /pedidos/1/status                -> 200
GET     /relatorios/vendas               -> 401 sem token · 200 com X-Admin-Token
DELETE  /produtos/11                     -> 200
POST    /admin/query · /admin/reset-db   -> 401 sem token
POST    /admin/query  (com token)        -> 403  (ENABLE_ADMIN_SQL desligado)
```

**Projeto 2** — `ADMIN_TOKEN=tok123 npm start`
```
> node src/app.js
[WARN] PAYMENT_GATEWAY_KEY não definida; usando valor aleatório (apenas desenvolvimento)
[INFO] LMS API rodando na porta 3000
POST   /api/checkout  (sucesso, api.http)        -> 200  {"msg":"Sucesso","enrollment_id":2}
POST   /api/checkout  (recusado, api.http)       -> 400  Pagamento recusado
POST   /api/checkout  (card numérico)            -> 400  Cartão inválido       (antes: derrubava o processo)
POST   /api/checkout  (curso 99)                 -> 404  Curso não encontrado
GET    /api/admin/financial-report               -> 401 sem token · 200 com token (mesmo formato de antes)
DELETE /api/users/1                              -> 401 sem token · 200 com token (remove matrículas/pagamentos juntos)
[INFO] Processando pagamento de 497 no cartão final 4444    (antes: cartão completo + chave do gateway)
```

**Projeto 3** — `python seed.py && python app.py`
```
python -W error::DeprecationWarning seed.py   →  3 usuários · 4 categorias · 10 tasks   (nenhum warning)
 * Debug mode: off
GET    / · /health                    -> 200 · 200
GET    /tasks · /tasks/1 · /tasks/stats -> 200 · 200 · 200
GET    /tasks/999                     -> 404
GET    /tasks/search?q=a&status=pending -> 200
GET    /tasks/search?priority=x       -> 400  (antes: 500)
POST   /tasks                         -> 201
POST   /tasks  (priority "alta")      -> 400  (antes: 500)
PUT    /tasks/1                       -> 200
GET    /users · /users/2 · /users/2/tasks -> 200 · 200 · 200   (sem password)
POST   /users · PUT /users/2          -> 201 · 200
POST   /login                         -> 200  {"token":"eyJ1aWQiOjJ9.ar1soA...", ...}   (token assinado)
GET    /reports/summary · /reports/user/1 -> 200 · 200
GET    /categories · POST · PUT       -> 200 · 201 · 200
DELETE /tasks/2 · /categories/4       -> 200 · 200
DELETE /users/3                       -> 401 sem token · 200 com token de admin
grep: datetime.utcnow = 0 · .query.get( = 0 · hashlib.md5 = 0 · except: = 0 · debug=True = 0
```

O resumo completo de cada refatoração, com a lista de mudanças de contrato, está em `<projeto>/docs/refactor-summary.md`.

### Como a skill se comportou em stacks diferentes

- **Python monolítico (P1):** criou `src/` com todas as camadas e manteve `app.py` na raiz como lançador, para preservar `python app.py`. Aplicou SQL parametrizado, `werkzeug.security` para as senhas e conexão por requisição em `flask.g`.
- **Node/Express (P2):** a mudança principal foi o fluxo assíncrono. Criou um wrapper Promise sobre o `sqlite3`, com `transaction()`, e reescreveu o checkout e o relatório com `async/await`, trocando o N+1 por um único `LEFT JOIN`. Para as senhas usou `crypto.scrypt` nativo, sem adicionar dependência. Classificou o uso da API de callbacks como padrão legado, e não como API removida.
- **Python parcialmente organizado (P3):** não moveu nada para `src/`. Manteve `models/`, `routes/` e `services/`, adicionou `config/`, `controllers/` e `middlewares/` e reaproveitou código morto (`helpers.py`, `Task.is_overdue`) em vez de duplicar. Foi o único projeto com APIs deprecated reais, e ele as substituiu.
- **O que se repetiu nas 3 stacks:** o mesmo template de relatório, a mesma cadeia F→AP→PB, o mesmo baseline e a mesma comparação antes/depois, e a documentação das mudanças de contrato. Isso mostra que o comportamento vem da skill, e não do projeto.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://code.claude.com/docs) instalado e autenticado (testado com a v2.1.284 e o modelo Opus 5.5)
- Python 3.12+ com `venv` (projetos 1 e 3)
- Node.js 18+ e npm (projeto 2, testado com o Node 22)
- `curl` (usado na validação)

### Executar a skill

A skill fica **dentro de cada projeto** (`<projeto>/.claude/skills/refactor-arch/`). Por isso **abra o Claude Code dentro da pasta do projeto**: aberto na raiz do repositório, ele não encontra a skill.

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução:
1. **Fase 1** imprime o resumo da stack.
2. **Fase 2** imprime o relatório e pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Revise e responda `y`.
3. **Fase 3** salva `docs/audit-report.md`, faz o baseline, refatora, valida e grava `docs/refactor-summary.md`.
4. Revise as mudanças (`git status`, que devem estar fora do staging) e faça o commit. Copie `docs/audit-report.md` para `reports/audit-project-N.md`.

Para usar a skill em outro projeto, copie a pasta: `cp -r code-smells-project/.claude <outro-projeto>/`.

### Validar que a refatoração funcionou

**Projeto 1**
```bash
cd code-smells-project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
rm -f loja.db                                   # banco antigo tem senhas em texto puro
ADMIN_TOKEN=tok123 .venv/bin/python app.py &
curl -s localhost:5000/produtos | head -c 200
curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
     -d '{"email":"admin@loja.com","senha":"admin123"}'
curl -s localhost:5000/relatorios/vendas -H 'X-Admin-Token: tok123'
```

**Projeto 2**
```bash
cd ecommerce-api-legacy
npm install
ADMIN_TOKEN=tok123 npm start &
# use as requisições de api.http (a variável @adminToken define o header X-Admin-Token)
curl -s -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
     -d '{"usr":"Gui","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
curl -s localhost:3000/api/admin/financial-report -H 'X-Admin-Token: tok123'
```

**Projeto 3**
```bash
cd task-manager-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
rm -f instance/tasks.db && .venv/bin/python seed.py
.venv/bin/python app.py &
curl -s localhost:5000/tasks | head -c 200
curl -s localhost:5000/reports/summary | head -c 200
curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
     -d '{"email":"joao@email.com","password":"1234"}'
```

Variáveis de ambiente suportadas por projeto: veja o `.env.example` de cada um (`SECRET_KEY`, `ADMIN_TOKEN`, `PORT`, `CORS_ORIGINS`, …). Sem `SECRET_KEY`, um valor aleatório é gerado a cada boot, só para desenvolvimento.
