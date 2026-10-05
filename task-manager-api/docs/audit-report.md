```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1160 lines of code
Date:    2026-10-05

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 6 | LOW: 4

## Findings

### F01 [CRITICAL] Credenciais e segredos hardcoded (AP-01)
File: app.py:13
File: services/notification_service.py:7-10
Description: SECRET_KEY definida como literal 'super-secret-key-123' em app.config; NotificationService.__init__ fixa host SMTP, usuário 'taskmanager@gmail.com' e self.email_password = 'senha123' no código. Routes: nenhuma
Impact: qualquer pessoa com acesso ao repositório obtém a chave de assinatura e a senha da conta de e-mail; trocar os segredos exige novo deploy.
Recommendation: ler SECRET_KEY e configuração SMTP de variáveis de ambiente num módulo config/settings, com .env.example sem valores reais (PB-01).

### F02 [CRITICAL] Senhas com hash MD5 sem salt (AP-04)
File: models/user.py:3, 27-32
File: seed.py:19, 26, 33
Description: User.set_password grava hashlib.md5(pwd.encode()).hexdigest() e check_password compara o MD5 com ==; o seed cria usuários com senhas '1234', 'abcd' e 'pass'. Routes: POST /users, PUT /users/<id>, POST /login
Impact: um vazamento do banco expõe todas as senhas em segundos (MD5 sem salt é quebrado por rainbow tables); a comparação não é em tempo constante.
Recommendation: usar werkzeug.security.generate_password_hash/check_password_hash, que já vem com o Flask (PB-06).

### F03 [CRITICAL] Hash de senha devolvido nas respostas da API (AP-06)
File: models/user.py:21
File: routes/user_routes.py:33, 85, 129, 209
Description: User.to_dict inclui 'password': self.password, e esse dict é devolvido por get_user, create_user, update_user e no campo 'user' do login. Routes: GET /users/<id>, POST /users, PUT /users/<id>, POST /login
Impact: qualquer cliente lê o hash MD5 de qualquer usuário (combinado com F02, recupera a senha em texto puro).
Recommendation: remover password da serialização de User e nunca serializar campos sensíveis (PB-06).

### F04 [CRITICAL] Endpoints administrativos e destrutivos sem autenticação (AP-05)
File: routes/user_routes.py:10, 42-78, 92-125, 134-151
File: routes/task_routes.py:225-238
File: routes/report_routes.py:12, 103, 211-223
Description: nenhuma rota verifica identidade ou permissão. Qualquer cliente anônimo lista todos os usuários e e-mails, cria usuário com role='admin' (create_user aceita role do body, linha 52), promove a si mesmo via PUT com 'role'/'active', apaga usuários (com todas as tasks deles), tasks e categorias, e lê relatórios de produtividade de todos. Routes: GET /users, POST /users, PUT /users/<id>, DELETE /users/<id>, DELETE /tasks/<id>, DELETE /categories/<id>, GET /reports/summary, GET /reports/user/<id>
Impact: escalonamento de privilégio trivial e destruição/leitura de todos os dados por qualquer pessoa na rede.
Recommendation: middleware de autenticação por token assinado e checagem de role admin nas operações de gestão de usuários (PB-13).

### F05 [CRITICAL] God File: relatórios e CRUD de categorias no mesmo blueprint (AP-03)
File: routes/report_routes.py:1-223
Description: report_routes.py registra rotas, faz todas as queries ORM e calcula agregações (summary_report tem 90 linhas: 12 contagens, cálculo de atraso, produtividade por usuário) e ainda abriga o CRUD completo de categorias (linhas 157-223), um domínio diferente, no blueprint 'reports'. Routes: GET /reports/summary, GET /reports/user/<id>, GET /categories, POST /categories, PUT /categories/<id>, DELETE /categories/<id>
Impact: impossível testar regra de relatório sem HTTP; mudar categorias mexe no arquivo de relatórios; o domínio fica escondido onde ninguém procura.
Recommendation: separar em rotas finas de reports e categories, controllers e um service de relatórios (PB-03, PB-04).

### F06 [HIGH] Autenticação falsa: token previsível e nunca verificado (AP-12)
File: routes/user_routes.py:207-211
File: app.py:13
Description: login devolve 'token': 'fake-jwt-token-' + str(user.id); nenhuma rota lê ou valida token, e a SECRET_KEY nunca é usada para assinar nada.
Impact: o token não protege nada, e qualquer um forja o "token" de outro usuário só trocando o id.
Recommendation: emitir token assinado (itsdangerous, já incluído no Flask) com expiração e validá-lo num decorator de auth (PB-13).

### F07 [HIGH] Regra de negócio e queries nas rotas (Fat Routes) (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 240-271, 273-299
File: routes/user_routes.py:42-90, 92-132, 134-151, 153-183
Description: os handlers validam o body, consultam o ORM, calculam atraso, montam o dict campo a campo, calculam completion_rate e fazem commit/rollback. get_tasks tem 53 linhas, create_task 70, update_task 68. delete_user apaga as tasks do usuário em loop dentro da rota.
Impact: regras de domínio só testáveis via HTTP; qualquer mudança de regra exige editar vários handlers.
Recommendation: rotas apenas delegam a controllers; regras (atraso, validação, estatísticas) vão para models/services (PB-04).

### F08 [HIGH] Configuração insegura: debug ligado e CORS aberto (AP-10)
File: app.py:15, 34
Description: app.run(debug=True, host='0.0.0.0', port=5000) liga o debugger do Werkzeug escutando em todas as interfaces; CORS(app) libera qualquer origem.
Impact: o console do debugger permite execução remota de código; qualquer site pode chamar a API pelo navegador da vítima.
Recommendation: DEBUG, HOST, PORT e CORS_ORIGINS vindos de config/env com padrões seguros (debug off) (PB-01).

### F09 [HIGH] Estado mutável acumulado em memória no NotificationService (AP-08)
File: services/notification_service.py:6, 31-36, 43-48
Description: self.notifications é uma lista em memória que recebe um append a cada notify_task_assigned e nunca é limpa; get_notifications varre a lista inteira.
Impact: vazamento de memória e dados perdidos a cada restart ou divergentes entre workers; testes ficam interdependentes.
Recommendation: remover o estado acumulado (ou persistir no banco) e tornar o serviço sem estado, recebendo a config por injeção (PB-05).

### F10 [HIGH] Acoplamento forte: app global com efeitos colaterais no import e SMTP concreto (AP-09)
File: app.py:9-31
File: services/notification_service.py:15-20
File: seed.py:2
Description: o app é criado no nível do módulo, com config literal e db.create_all() executado no import (seed.py importa app para reutilizar isso); NotificationService instancia smtplib.SMTP diretamente, sem como injetar outro transporte.
Impact: impossível criar o app com outra config (teste, outro banco) ou trocar o envio de e-mail por um fake.
Recommendation: application factory create_app(config) como composition root; serviços recebem dependências no construtor (PB-05).

### F11 [MEDIUM] Queries N+1 e contagens repetidas (AP-13)
File: routes/task_routes.py:41-57, 275-279
File: routes/user_routes.py:22
File: routes/report_routes.py:15-28, 55-56, 163
Description: get_tasks faz User.query.get e Category.query.get para cada task; get_users acessa o lazy u.tasks no loop; summary_report dispara 12 COUNTs separados mais um filter_by por usuário; get_categories faz um COUNT por categoria; task_stats faz 5 COUNTs mais um Task.query.all().
Impact: o número de queries cresce linearmente com os dados, e a latência dos endpoints de listagem e relatório cresce junto.
Recommendation: GROUP BY para contagens e eager loading (joinedload/selectinload) para relacionamentos (PB-07).

### F12 [MEDIUM] Lógica e validação duplicadas, com utilitários existentes ignorados (AP-15)
File: routes/task_routes.py:17-28, 30-39, 71-80, 92-144, 166-213, 283-287
File: routes/user_routes.py:61, 106, 162-180
File: routes/report_routes.py:34-36, 132-135
File: models/task.py:38-60
File: utils/helpers.py:19-23, 57-108, 110-116
Description: o cálculo de "overdue" é reimplementado 6 vezes, embora Task.is_overdue exista e nunca seja usado; get_tasks reconstrói Task.to_dict campo a campo; as validações de create_task e update_task são duplicadas (process_task_data, que faz o mesmo, não é usado); a lista de status aparece em 4 lugares; a regex de e-mail aparece 3 vezes.
Impact: as regras divergem (create aceita só YYYY-MM-DD, parse_date aceita DD/MM/YYYY), e corrigir um bug exige achar todas as cópias.
Recommendation: centralizar as regras no model/validador de domínio e as constantes num módulo único (PB-12).

### F13 [MEDIUM] Validação de entrada fraca causando 500 e dados inválidos (AP-16)
File: routes/task_routes.py:104, 113, 166-171, 181-184, 260-264
File: routes/report_routes.py:196-202, 173-180
File: routes/user_routes.py:102-103, 124-125
Description: priority < 1 com priority string lança TypeError (500); len(data['title']) quebra com não-string; int(priority)/int(user_id) na busca quebram com valor inválido; update_category faz 'name' in data com data None (TypeError) e não valida a cor (is_valid_color existe e não é usado); update_user aceita name vazio e active de qualquer tipo.
Impact: entradas inválidas viram 500 ou ficam gravadas no banco.
Recommendation: validar tipo e formato num validador por entidade e devolver 400 com a mensagem (PB-12).

### F14 [MEDIUM] Tratamento de erro espalhado e engolido, sem handler central (AP-17)
File: routes/task_routes.py:62-63, 137, 151-154, 204, 236
File: routes/user_routes.py:87-90, 130, 149
File: routes/report_routes.py:186, 207, 221
File: utils/helpers.py:46, 49, 88
File: app.py:9-34
Description: 12 blocos except: sem tipo e try/except com rollback copiados em cada handler; get_tasks engole qualquer exceção como 'Erro interno'; não existe @app.errorhandler, então 404/405 voltam como HTML.
Impact: bugs ficam ocultos (inclusive KeyboardInterrupt/SystemExit são capturados), as respostas de erro são inconsistentes e não há log útil.
Recommendation: exceções de domínio e error handler central que devolve JSON; remover os except: soltos (PB-09).

### F15 [MEDIUM] Exclusão de categoria deixa tasks órfãs (AP-14)
File: routes/report_routes.py:211-223
File: models/task.py:14
Description: delete_category apaga a categoria sem tratar tasks.category_id que a referenciam; o SQLite não aplica a FK, pois PRAGMA foreign_keys está desligado.
Impact: tasks apontando para categoria inexistente; category_name e contagens ficam inconsistentes.
Recommendation: desassociar (category_id = NULL) as tasks na mesma transação da exclusão (PB-10).

### F16 [MEDIUM] APIs deprecated em uso: Query.get e datetime.utcnow (AP-22)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 (Query.get); 31, 72, 215, 285 (utcnow)
File: routes/user_routes.py:29, 94, 136, 155 (Query.get); 172 (utcnow)
File: routes/report_routes.py:105, 192, 213 (Query.get); 35, 42, 45, 71, 133 (utcnow)
File: models/task.py:15-16, 52
File: models/user.py:14
File: models/category.py:11
File: services/notification_service.py:35
File: utils/helpers.py:38
Description: Model.query.get(id) é API legada no SQLAlchemy 2.x (emite LegacyAPIWarning) e datetime.utcnow está deprecated desde o Python 3.12 (DeprecationWarning no 3.14 instalado). Severidade elevada para MEDIUM porque ambas já emitem warning nas versões em uso.
Impact: warnings em runtime e quebra quando forem removidas.
Recommendation: db.session.get(Model, id) e helper utcnow() baseado em datetime.now(timezone.utc) (PB-11).

### F17 [LOW] Magic numbers e strings (AP-18)
File: routes/task_routes.py:96-100, 104, 110, 113, 177, 182
File: routes/user_routes.py:52, 64, 71, 115, 120
File: routes/report_routes.py:24-28, 45, 129, 180
File: app.py:34
Description: limites de título 3/200, prioridade 1-5, senha mínima 4, "alta prioridade" <= 2, janela de 7 dias, '#000000', listas de status e roles inline e porta 5000; as constantes em utils/helpers.py:110-116 existem e não são usadas.
Impact: regra escondida em literais e alterações inconsistentes.
Recommendation: constantes nomeadas num módulo de domínio/config (PB-12).

### F18 [LOW] Nomenclatura ruim (AP-19)
File: routes/report_routes.py:24-28
File: models/task.py:45
File: models/user.py:27, 31
Description: contagens p1..p5 em summary_report, parâmetros p e pwd, variáveis de uma letra (u, t, c) fora de loops curtos.
Impact: leitura e manutenção mais difíceis.
Recommendation: nomes descritivos (count_by_priority, password) (PB-12).

### F19 [LOW] Código morto, imports e dependências não usados (AP-20)
File: app.py:7
File: routes/task_routes.py:7
File: routes/user_routes.py:6
File: routes/report_routes.py:7-8
File: models/task.py:3, 38-48
File: models/user.py:34-38
File: utils/helpers.py:1-116
File: services/notification_service.py:1-48
File: requirements.txt:4-6
Description: imports sem uso (os, sys, json, time, hashlib, math, format_date, calculate_percentage); Task.validate_status/validate_priority e User.is_admin nunca chamados; utils/helpers.py e NotificationService inteiros sem referência; marshmallow, requests e python-dotenv declarados e nunca importados.
Impact: ruído, falsa impressão de que existe validação ou notificação, e dependências extras para auditar.
Recommendation: remover o código morto e as dependências sem uso, ou passar a usá-los de fato (PB-14).

### F20 [LOW] print usado como logging (AP-21)
File: routes/task_routes.py:149, 153, 219, 234
File: routes/user_routes.py:83, 89, 147
File: services/notification_service.py:21, 24
File: utils/helpers.py:39, 41
Description: eventos e erros de aplicação registrados com print(f"...").
Impact: sem níveis, sem destino configurável, e mensagens de erro misturadas no stdout.
Recommendation: módulo logging com logger por módulo (PB-14).

## Deprecated APIs
| API usada | Local | Versão detectada | Substituir por |
|---|---|---|---|
| Model.query.get(id) | routes/task_routes.py:42 (+15 outras, ver F16) | Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.x | db.session.get(Model, id) |
| datetime.utcnow() | models/task.py:15 (+17 outras, ver F16) | Python 3.14.4 | datetime.now(timezone.utc) |

## Architecture verdict
Current: Parcialmente em camadas — pastas existem, mas as rotas concentram queries, regras e serialização
Target:  MVC — rotas finas que delegam a controllers, regras nos models/services, config e auth centralizados numa application factory

================================
Total: 20 findings
================================
```
