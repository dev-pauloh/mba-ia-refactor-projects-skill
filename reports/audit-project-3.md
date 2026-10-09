# Audit Report — Projeto 3: task-manager-api (Python/Flask)

> Saída da Fase 2 da skill `/refactor-arch`, executada em `task-manager-api/` (Claude Code 2.1.284, Opus 5.5). Execução com a versão final da skill (recomendação cobre todo o impacto de cada finding).

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.14 + Flask 3.0.0
Files:   15 analyzed | ~1160 lines of code
Date:    2026-10-09

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 7 | LOW: 4

## Findings

### F01 [CRITICAL] Endpoints sensíveis e destrutivos sem autenticação nem autorização (AP-05)
File: routes/task_routes.py:11, 65, 85, 156, 225, 240, 273
File: routes/user_routes.py:10, 27, 42, 92, 119-125, 134-151, 153
File: routes/report_routes.py:12, 103, 157, 167, 190, 211
Description: nenhuma rota tem decorator ou middleware de autenticação (não existe nenhum no projeto). create_user aceita `role` do body (user_routes.py:52, 71-78), então qualquer um cria uma conta 'admin'; update_user altera `role` e `active` de qualquer usuário (user_routes.py:119-125); delete_user apaga o usuário e todas as suas tasks (user_routes.py:134-151); get_users, get_user, user_report e summary_report devolvem nome, e-mail, role e produtividade de todos os usuários. Routes: GET /tasks, GET /tasks/<int:task_id>, POST /tasks, PUT /tasks/<int:task_id>, DELETE /tasks/<int:task_id>, GET /tasks/search, GET /tasks/stats, GET /users, GET /users/<int:user_id>, POST /users, PUT /users/<int:user_id>, DELETE /users/<int:user_id>, GET /users/<int:user_id>/tasks, GET /reports/summary, GET /reports/user/<int:user_id>, GET /categories, POST /categories, PUT /categories/<int:cat_id>, DELETE /categories/<int:cat_id>
Impact: qualquer cliente anônimo lista e consulta usuários (nome, e-mail, role), tasks, categorias e relatórios; cria contas com role 'admin'; promove ou desativa qualquer usuário; cria, altera e apaga qualquer task, categoria ou usuário (com todas as suas tasks).
Recommendation: criar um decorator de autenticação (token assinado de F05, usuário existente e ativo) e aplicá-lo às 19 rotas listadas, deixando públicas apenas GET /, GET /health e POST /login; adicionar autorização por papel: GET /users e GET /reports/summary exigem 'admin' ou 'manager'; POST /users e DELETE /users/<int:user_id> exigem 'admin'; PUT /users/<int:user_id> exige ser o próprio usuário ou 'admin', e só 'admin' pode alterar `role` e `active`; GET /users/<int:user_id>, GET /users/<int:user_id>/tasks e GET /reports/user/<int:user_id> exigem ser o próprio usuário ou 'admin'/'manager'; POST, PUT e DELETE de /categories exigem 'admin' ou 'manager'; as rotas de tasks e GET /categories exigem apenas usuário autenticado (PB-13).

### F02 [CRITICAL] Hash da senha devolvido nas respostas da API (AP-06)
File: models/user.py:16-25
File: routes/user_routes.py:33, 85, 129, 209
Description: User.to_dict inclui `'password': self.password` (models/user.py:21) e é usado para serializar get_user, create_user, update_user e login, então o hash MD5 da senha sai no JSON. Routes: GET /users/<int:user_id>, POST /users, PUT /users/<int:user_id>, POST /login
Impact: qualquer cliente obtém o hash MD5 da senha de qualquer usuário (e o próprio no login); com F03 esse hash é revertido em segundos por rainbow tables.
Recommendation: remover `password` da serialização pública de User (to_dict só com id, name, email, role, active, created_at) e exigir autenticação nas rotas listadas, exceto POST /login, conforme F01 (PB-06, PB-13).

### F03 [CRITICAL] Senhas armazenadas com MD5 sem salt e política de senha fraca (AP-04)
File: models/user.py:3, 27-32
File: routes/user_routes.py:64, 115
Description: set_password grava `hashlib.md5(pwd.encode()).hexdigest()` e check_password compara o MD5 (models/user.py:29, 32); create_user e update_user aceitam senhas com 4 caracteres (`len(password) < 4`). Routes: POST /users, PUT /users/<int:user_id>, POST /login
Impact: um vazamento do banco expõe todas as senhas (MD5 sem salt é quebrado por tabelas pré-computadas), com reuso em outros serviços; senhas de 4 caracteres caem por força bruta online em POST /login.
Recommendation: usar werkzeug.security.generate_password_hash/check_password_hash (já incluído no Flask, com salt e KDF lenta) em set_password/check_password, exigir mínimo de 8 caracteres em POST /users e PUT /users/<int:user_id> e exigir autenticação nas rotas listadas, exceto POST /login, conforme F01 (PB-06).

### F04 [CRITICAL] Segredos e configuração hardcoded (AP-01)
File: app.py:11-13
File: services/notification_service.py:7-10
Description: SECRET_KEY é o literal 'super-secret-key-123' (app.py:13); a URI do banco é fixa em 'sqlite:///tasks.db' (app.py:11); NotificationService fixa host, porta, usuário e senha SMTP ('taskmanager@gmail.com' / 'senha123'). Routes: nenhuma
Impact: qualquer pessoa com acesso ao repositório obtém a chave de assinatura (e, com ela, pode forjar tokens após F05) e a senha do e-mail; rotacionar segredos ou trocar o banco exige alterar código e fazer deploy.
Recommendation: criar config/settings.py que lê SECRET_KEY, DATABASE_URL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (e demais opções) de variáveis de ambiente via python-dotenv, gerar uma SECRET_KEY aleatória por processo quando ausente (com aviso no log), injetar as configurações SMTP no NotificationService e documentar tudo em .env.example sem valores reais (PB-01).

### F05 [HIGH] Token de login falso e previsível (AP-12)
File: routes/user_routes.py:207-211
Description: login devolve `'token': 'fake-jwt-token-' + str(user.id)`, sem assinatura nem expiração, e nenhuma rota valida esse token. Routes: POST /login
Impact: o token não prova identidade: qualquer um forja o token de qualquer usuário trocando o id, e a API não tem como autenticar requisições.
Recommendation: emitir em POST /login um token assinado com SECRET_KEY e com expiração (itsdangerous.URLSafeTimedSerializer, dependência do próprio Flask), mantendo a chave `token` na resposta, e validá-lo no decorator de autenticação de F01 via header `Authorization: Bearer <token>`, rejeitando token inválido, expirado ou de usuário inativo com 401 (PB-13).

### F06 [HIGH] Debug ativo, bind em todas as interfaces e CORS aberto (AP-10)
File: app.py:15, 34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger interativo do Werkzeug exposto na rede e `CORS(app)` libera qualquer origem. O debugger é alcançável por qualquer exceção não tratada, por exemplo `priority` string em POST /tasks e PUT /tasks/<int:task_id> (TypeError em task_routes.py:113, 182), `priority=abc` em GET /tasks/search (ValueError em task_routes.py:261), e-mail ou senha não-string em POST /users e PUT /users/<int:user_id> (user_routes.py:61, 64, 106, 115) e PUT /categories/<int:cat_id> sem body (TypeError em report_routes.py:197). Routes: POST /tasks, PUT /tasks/<int:task_id>, GET /tasks/search, POST /users, PUT /users/<int:user_id>, PUT /categories/<int:cat_id> (debugger); CORS aberto em todas as rotas do inventário
Impact: o debugger do Werkzeug exibe stack trace e código-fonte e oferece console Python (execução remota de código) a quem provocar uma exceção; qualquer site pode chamar a API e ler as respostas a partir do navegador de um usuário.
Recommendation: ler DEBUG (padrão False), HOST (padrão 127.0.0.1) e PORT (padrão 5000) de config/settings.py; restringir CORS às origens de CORS_ORIGINS (vazio = nenhuma origem cruzada); registrar error handlers JSON (F09) e validar tipos (F08) para que as rotas listadas respondam 400/500 em JSON em vez de abrir o debugger (PB-01).

### F07 [HIGH] Regra de negócio, acesso a dados e serialização dentro das rotas (AP-07)
File: routes/task_routes.py:12-63, 86-154, 157-223, 241-271, 274-299
File: routes/user_routes.py:43-90, 93-132, 135-151, 154-183
File: routes/report_routes.py:13-101, 104-155, 157-223
Description: os handlers fazem tudo: leem request, validam, consultam o ORM, calculam atraso, contagens e percentuais (task_stats, summary_report, user_report), aplicam a regra de exclusão em cascata de delete_user e montam o JSON campo a campo; não há camada de controller/service, e report_routes.py mistura relatórios com o CRUD de categorias (report_routes.py:157-223). Routes: nenhuma (problema estrutural)
Impact: regras só são testáveis via HTTP, cada endpoint reimplementa a mesma lógica (F12) e qualquer mudança de regra exige alterar vários handlers.
Recommendation: separar em camadas: routes/*_routes.py só mapeiam URL→controller; controllers/ leem e validam o request e formatam a resposta; services/ concentram regras (atraso, estatísticas, relatórios, cascatas) e acesso ao ORM; mover o CRUD de categorias para controllers/category_controller.py + routes/category_routes.py (PB-04).

### F08 [MEDIUM] Validação de entrada ausente ou só de presença (AP-16)
File: routes/task_routes.py:92-114, 108, 140-144, 166-184, 209-213, 260-264
File: routes/user_routes.py:49-72, 102-103, 114-125
File: routes/report_routes.py:178-180, 196-202
Description: os campos do body são usados sem checar tipo: `priority < 1` e `len(title)` quebram com string/número (task_routes.py:96, 113, 167, 182); `int(priority)` e `int(user_id)` da query string sem tratamento (task_routes.py:261, 264); `tags` aceita qualquer tipo; update_user aceita `name` vazio e `active` não booleano (user_routes.py:102-103, 124-125) e chama `len`/`re.match` em valores não-string; update_category usa `'name' in data` sem checar se há body (report_routes.py:196-197) e nenhuma rota valida `color` (is_valid_color existe e não é usado). Routes: POST /tasks, PUT /tasks/<int:task_id>, GET /tasks/search, POST /users, PUT /users/<int:user_id>, POST /categories, PUT /categories/<int:cat_id>
Impact: entradas malformadas geram 500 (e abrem o debugger, F06) em vez de 400, e dados inválidos são gravados (categoria com cor 'xyz', usuário com nome vazio, tags com tipo arbitrário).
Recommendation: criar validadores centralizados que checam presença, tipo, faixa e formato (title string 3-200, status, priority inteiro 1-5, due_date YYYY-MM-DD, tags lista de strings ou string, ids inteiros, e-mail, senha, role, active booleano, name não vazio, color #RRGGBB, body JSON obrigatório) e usá-los em todos os controllers das rotas listadas, respondendo 400 com mensagem (PB-12).

### F09 [MEDIUM] Erros engolidos com except genérico e sem handler central (AP-17)
File: routes/task_routes.py:62-63, 137, 151-154, 204, 221-223, 236-238
File: routes/user_routes.py:87-90, 130-132, 149-151
File: routes/report_routes.py:186-188, 207-209, 221-223
File: utils/helpers.py:46, 49, 88
Description: 12 blocos `except:` sem tipo e `except Exception as e` com print; get_tasks embrulha o handler inteiro e devolve 'Erro interno' sem registrar a causa (task_routes.py:62-63); não existe `@app.errorhandler`, então 404/405/500 fora desses blocos saem como HTML. Routes: GET /tasks, POST /tasks, PUT /tasks/<int:task_id>, DELETE /tasks/<int:task_id>, POST /users, PUT /users/<int:user_id>, DELETE /users/<int:user_id>, POST /categories, PUT /categories/<int:cat_id>, DELETE /categories/<int:cat_id>
Impact: falhas reais (banco, bug) somem sem log nem stack trace, mascaradas como 500 genérico; clientes recebem HTML em vez de JSON em erros não previstos.
Recommendation: definir exceções de domínio (ValidationError, NotFoundError, ConflictError, AuthError) lançadas por services/controllers, registrar error handlers JSON centrais (400, 401, 403, 404, 405, 409, 500) que fazem rollback da sessão e logam a stack, e remover todos os `except:` genéricos (PB-09).

### F10 [MEDIUM] Exclusão de categoria deixa tasks órfãs (AP-14)
File: routes/report_routes.py:211-223
File: models/task.py:13-14
Description: delete_category apaga a categoria sem tratar as tasks que a referenciam; as FKs não têm `ondelete` e o SQLite roda sem `PRAGMA foreign_keys=ON`, então nada impede a referência pendente. Routes: DELETE /categories/<int:cat_id>
Impact: tasks continuam com `category_id` de uma categoria inexistente (category_name vira null em GET /tasks), corrompendo filtros e relatórios.
Recommendation: no service de categorias, anular `tasks.category_id` e apagar a categoria na mesma transação; declarar `ondelete='SET NULL'` em Task.category_id e `ondelete='CASCADE'` em Task.user_id e ativar `PRAGMA foreign_keys=ON` nas conexões SQLite (PB-10).

### F11 [MEDIUM] Queries N+1 e contagens repetidas (AP-13)
File: routes/task_routes.py:41-57, 275-287
File: routes/user_routes.py:22
File: routes/report_routes.py:15-28, 55-56, 161-163
Description: get_tasks faz `User.query.get` e `Category.query.get` por task; get_users acessa o relacionamento lazy `len(u.tasks)` por usuário; summary_report dispara 12 `.count()` em sequência e uma query de tasks por usuário; get_categories faz um `count()` por categoria; task_stats faz 5 contagens mais a leitura de todas as tasks. Routes: GET /tasks, GET /users, GET /reports/summary, GET /categories, GET /tasks/stats
Impact: o número de queries cresce linearmente com tasks, usuários e categorias, degradando a latência dessas rotas.
Recommendation: usar eager loading (joinedload de user/category) em GET /tasks e agregações com GROUP BY (tasks por status, por prioridade, por usuário e por categoria) em GET /users, GET /reports/summary, GET /categories e GET /tasks/stats (PB-07).

### F12 [MEDIUM] Regras e serialização duplicadas, com utilitários existentes ignorados (AP-15)
File: routes/task_routes.py:17-39, 71-80, 96-100, 110-114, 166-184, 283-287
File: routes/user_routes.py:15-23, 61, 106, 162-180
File: routes/report_routes.py:33-36, 132-135
File: models/task.py:38-60
File: utils/helpers.py:19-23, 57-116
Description: o cálculo de "atrasado" é copiado 6 vezes enquanto Task.is_overdue (models/task.py:50-60) não é usado; a lista de status aparece em 4 lugares; validações de título/status/prioridade de create e update são duplicadas; o regex de e-mail é repetido (user_routes.py:61, 106) apesar de validate_email; a task é serializada campo a campo (task_routes.py:17-28, user_routes.py:162-169) duplicando Task.to_dict; process_task_data e as constantes de helpers.py nunca são usados. Routes: nenhuma
Impact: uma mudança de regra (ex.: novo status) precisa ser replicada em vários pontos, e as cópias já divergem (create valida título vazio, update não).
Recommendation: uma única fonte para cada regra: Task.is_overdue e to_dict nos models, constantes de domínio em um módulo único, validadores compartilhados entre create/update (F08), reaproveitados por todos os controllers/services (PB-12).

### F13 [MEDIUM] NotificationService acoplado ao SMTP e com estado em memória (AP-09)
File: services/notification_service.py:4-48
Description: o serviço instancia `smtplib.SMTP` diretamente em send_email (linha 15), lê credenciais fixas (F04) e acumula notificações na lista `self.notifications` (linhas 6, 31-36) que só cresce; hoje não é importado por nenhuma rota. Severidade ajustada de HIGH para MEDIUM porque o serviço não está ligado a nenhum fluxo em execução. Routes: nenhuma
Impact: impossível testar sem servidor SMTP real ou trocar o transporte sem editar o serviço; a lista em memória vaza memória, some a cada reinício e não é compartilhada entre processos.
Recommendation: receber as configurações SMTP (de config/settings.py) e uma fábrica de conexão SMTP por injeção no construtor, remover a lista `notifications`/get_notifications e registrar envios com logging (PB-05).

### F14 [MEDIUM] APIs deprecated: Query.get e datetime.utcnow (AP-22)
File: routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285
File: routes/user_routes.py:29, 94, 136, 155, 172
File: routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213
File: models/task.py:15, 16, 52
File: models/user.py:14
File: models/category.py:11
File: utils/helpers.py:38
File: services/notification_service.py:35
File: seed.py:66, 67, 69, 70, 74
Description: `Model.query.get(id)` é API legada no SQLAlchemy 2.x (instalado 2.1.1) e emite LegacyAPIWarning; `datetime.utcnow()` está deprecated desde o Python 3.12 (instalado 3.14) e emite DeprecationWarning. Severidade MEDIUM porque ambos já emitem warning nas versões instaladas e estão marcados para remoção. Routes: nenhuma
Impact: warnings a cada requisição e quebra no próximo upgrade que remover as APIs.
Recommendation: substituir por `db.session.get(Model, id)` e por um helper de relógio baseado em `datetime.now(timezone.utc)` (normalizado para UTC naive, preservando o formato atual das datas) em models, services e seed (PB-11).

### F15 [LOW] Magic numbers e strings de domínio (AP-18)
File: routes/task_routes.py:96, 99, 104, 110, 113, 167, 169, 177, 182
File: routes/user_routes.py:64, 71, 115, 120
File: routes/report_routes.py:45, 129, 180
File: models/task.py:11-12, 39, 46
File: models/category.py:10
File: app.py:34
Description: limites de título (3/200), faixa de prioridade (1/5), prioridade padrão 3, `priority <= 2` como "alta prioridade", janela de 7 dias, senha mínima 4, cor '#000000', porta 5000 e as listas de status/roles aparecem como literais; as constantes de utils/helpers.py:110-116 existem mas não são usadas. Routes: nenhuma
Impact: regras de negócio escondidas em literais, fáceis de alterar em um lugar e esquecer em outro.
Recommendation: constantes nomeadas em um módulo de domínio (status, roles, limites, prioridade padrão, janela de atividade, cor padrão) e porta em config (PB-12).

### F16 [LOW] Nomes sem significado (AP-19)
File: routes/report_routes.py:24-28, 55, 161
File: routes/task_routes.py:16, 51
File: routes/user_routes.py:14
File: models/category.py:14
Description: p1..p5 para contagens por prioridade, `u`, `t`, `c`, `cat` e `d` como nomes de variáveis em loops e handlers longos. Routes: nenhuma
Impact: leitura e revisão mais lentas; nomes numerados escondem o significado (p1 = "critical").
Recommendation: renomear para nomes de domínio (por exemplo, contagem por prioridade em dicionário nomeado, user, task, category) durante a extração para services (PB-12).

### F17 [LOW] Imports, utilitários e dependências não usados (AP-20)
File: app.py:7
File: routes/task_routes.py:7
File: routes/user_routes.py:6
File: routes/report_routes.py:7-8
File: models/task.py:3, 38-48
File: models/user.py:34-38
File: utils/helpers.py:3-7, 9-55, 57-108, 110-116
File: requirements.txt:4-6
Description: `os, sys, json` (app.py), `json, os, sys, time` (task_routes.py), `hashlib, json` (user_routes.py), `format_date, calculate_percentage, json` (report_routes.py) e `json` (models/task.py) são importados sem uso; Task.validate_status/validate_priority, User.is_admin e todas as funções e constantes de utils/helpers.py não são chamadas; marshmallow, requests e python-dotenv estão no requirements e não são importados. Routes: nenhuma
Impact: ruído na leitura, falsa impressão de que existe validação centralizada e dependências instaladas sem necessidade (superfície de ataque maior).
Recommendation: remover imports e funções mortas, reaproveitar o que tiver valor (constantes, validação, is_overdue) nos novos módulos, remover marshmallow e requests do requirements e passar a usar python-dotenv na config (PB-14).

### F18 [LOW] print usado como logging (AP-21)
File: routes/task_routes.py:149, 153, 219, 234
File: routes/user_routes.py:83, 89, 147
File: services/notification_service.py:21, 24
File: utils/helpers.py:39, 41
Description: eventos de criação/atualização/exclusão e erros são escritos com `print`, sem nível nem logger. Routes: nenhuma
Impact: impossível filtrar por nível, desligar ou enviar para um coletor; erros se misturam com mensagens informativas.
Recommendation: usar o módulo logging (logger por módulo, nível configurável por LOG_LEVEL) no lugar de print no código da aplicação (PB-14).

## Deprecated APIs
| API usada | Local | Versão detectada | Substituir por |
|---|---|---|---|
| `Model.query.get(id)` | routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | SQLAlchemy 2.1.1 / Flask-SQLAlchemy 3.1.1 | `db.session.get(Model, id)` |
| `datetime.utcnow()` / `default=datetime.utcnow` | models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; utils/helpers.py:38; services/notification_service.py:35; seed.py:66, 67, 69, 70, 74 | Python 3.14.4 | `datetime.now(timezone.utc)` |

## Architecture verdict
Current: Parcialmente em camadas — existem models/, routes/, services/ e utils/, mas as rotas concentram validação, ORM e regra de negócio (routes/task_routes.py:12-63), não há controllers, o serviço de notificação não é usado e a configuração está hardcoded (app.py:11-13).
Target:  MVC — criar config/, controllers/, services/ de domínio e middlewares (auth + error handler), deixando as rotas só como mapeamento URL→controller e os models só com dados e regras da entidade.

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
