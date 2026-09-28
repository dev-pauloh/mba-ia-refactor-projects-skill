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

> _Em construção (Etapa 2)._

## C) Resultados

> _Em construção (Etapa 3)._

## D) Como Executar

> _Em construção (Etapa 4)._
