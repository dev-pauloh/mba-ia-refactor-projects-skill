# Audit Report — Projeto 3: task-manager-api (Python/Flask)

> Saída da Fase 2 da skill `/refactor-arch`, executada em `task-manager-api/` (Claude Code 2.1.284, Opus 5.5).

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1160 lines of code
Date:    2026-09-30

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 5

## Findings

### F01 [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:13
File: services/notification_service.py:7-10
Description: SECRET_KEY definida como literal 'super-secret-key-123'; NotificationService fixa host SMTP, usuário 'taskmanager@gmail.com' e email_password = 'senha123' no construtor.
Impact: qualquer leitor do repositório obtém a chave de assinatura de sessão e a senha da conta de e-mail; rotacionar exige alterar código e fazer deploy.
Recommendation: centralizar em config/settings lendo variáveis de ambiente (SECRET_KEY, DATABASE_URL, SMTP_*) com .env.example sem valores reais (PB-01).

### F02 [CRITICAL] Senhas com hash MD5 sem salt (AP-04)
File: models/user.py:3, 27-32
Description: set_password grava hashlib.md5(pwd.encode()).hexdigest() e check_password compara o MD5 com ==.
Impact: um vazamento do banco revela as senhas por rainbow table/força bruta em segundos (seed usa '1234', 'abcd', 'pass').
Recommendation: usar werkzeug.security.generate_password_hash/check_password_hash (já dependência do Flask) (PB-06).

### F03 [CRITICAL] Hash de senha exposto nas respostas da API (AP-06)
File: models/user.py:16-25
File: routes/user_routes.py:33, 85, 129, 209
Description: User.to_dict inclui 'password': self.password e é devolvido por GET /users/<id>, POST /users, PUT /users/<id> e POST /login.
Impact: qualquer cliente obtém o hash (MD5, trivialmente reversível — F02) de qualquer usuário.
Recommendation: remover 'password' da serialização pública do usuário (PB-06).

### F04 [CRITICAL] Endpoints destrutivos e administrativos sem autenticação/autorização (AP-05)
File: routes/user_routes.py:52, 71, 119-122, 134-151
File: routes/task_routes.py:225-238
File: routes/report_routes.py:211-223
Description: DELETE /users/<id>, DELETE /tasks/<id> e DELETE /categories/<id> não verificam identidade; POST /users aceita 'role': 'admin' do próprio cliente e PUT /users/<id> permite trocar role/active de qualquer usuário.
Impact: qualquer cliente anônimo apaga usuários (com todas as suas tasks), escala privilégio para admin ou desativa contas.
Recommendation: exigir token assinado nas rotas de escrita sensíveis e checar role admin para gestão de usuários/roles (PB-13).

### F05 [HIGH] Autenticação falsa: token previsível e não verificado (AP-12)
File: routes/user_routes.py:207-211
Description: /login retorna 'token': 'fake-jwt-token-' + str(user.id); nenhuma rota do projeto valida esse token (não há decorator/middleware de auth).
Impact: o token é forjável por qualquer um e, de todo modo, inútil — a API é totalmente aberta.
Recommendation: emitir token assinado com SECRET_KEY (itsdangerous, já incluído no Flask) e decorator de verificação (PB-13).

### F06 [HIGH] Configuração insegura: debug ligado e CORS aberto (AP-10)
File: app.py:15, 34
Description: app.run(debug=True, host='0.0.0.0', port=5000) fixo e CORS(app) sem restrição de origens.
Impact: debugger do Werkzeug exposto na rede permite execução remota de código; qualquer origem web pode chamar a API.
Recommendation: ler DEBUG/HOST/PORT/CORS_ORIGINS de configuração com defaults seguros (PB-01).

### F07 [HIGH] Regra de negócio e acesso a dados nas rotas (Fat Routes) (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299
File: routes/user_routes.py:42-90, 153-183
File: routes/report_routes.py:12-101, 103-155, 157-223
Description: handlers validam payload, consultam ORM, calculam atraso, taxas de conclusão, contagens por status/prioridade e serializam manualmente (summary_report tem ~90 linhas); não existe camada de controller/service. O CRUD de categorias está no blueprint de relatórios.
Impact: regras só testáveis via HTTP, duplicadas entre endpoints (F11) e acopladas ao Flask; viola SRP.
Recommendation: extrair controllers/services por domínio (tasks, users, categories, reports) e deixar as rotas apenas delegando (PB-04).

### F08 [HIGH] Acoplamento forte e composição sem factory (AP-09 / AP-08)
File: app.py:9-31
File: seed.py:2
File: services/notification_service.py:5-20, 31-36
Description: a app é criada, configurada e faz db.create_all() no momento do import de app.py (seed.py depende disso); rotas usam db.session e models diretamente; NotificationService instancia smtplib.SMTP com config fixa e acumula self.notifications em memória indefinidamente.
Impact: impossível criar a app com outra config (testes, outro banco) ou substituir SMTP por fake; lista em memória cresce sem limite e não é compartilhada entre processos.
Recommendation: create_app() como composition root com config injetada; service de notificação recebendo config por parâmetro, sem estado acumulado (PB-05).

### F09 [MEDIUM] Queries N+1 e contagens repetidas (AP-13)
File: routes/task_routes.py:41-57, 275-279
File: routes/user_routes.py:22
File: routes/report_routes.py:15-28, 55-56, 161-163
Description: GET /tasks faz User.query.get e Category.query.get por task; GET /users acessa len(u.tasks) por usuário; summary faz 12 COUNTs separados e Task.query.filter_by(user_id=...) por usuário; GET /categories faz COUNT por categoria.
Impact: número de queries cresce linearmente com os dados; latência alta em bases reais.
Recommendation: eager loading (joinedload/selectinload) e agregações com GROUP BY (PB-07).

### F10 [MEDIUM] Exclusão sem integridade referencial (AP-14)
File: routes/report_routes.py:211-223
File: models/task.py:13-14, 20-21
Description: DELETE /categories/<id> apaga a categoria deixando tasks com category_id apontando para registro inexistente (SQLite sem FK enforcement, relacionamentos sem ondelete/cascade); delete_user remove tasks manualmente no handler.
Impact: tasks órfãs com category_id inválido; regra de cascata espalhada nas rotas.
Recommendation: tratar dependentes no service dentro da mesma transação (desvincular tasks da categoria; cascata de tasks do usuário) (PB-10).

### F11 [MEDIUM] Lógica e validação duplicadas (AP-15)
File: routes/task_routes.py:17-39, 71-80, 96-114, 166-184, 284-287
File: routes/user_routes.py:61, 106, 162-180
File: routes/report_routes.py:34-36, 132-135
File: models/task.py:38-60
File: utils/helpers.py:19-23, 57-108
Description: o cálculo de "overdue" aparece 6 vezes inline enquanto Task.is_overdue existe sem uso; serialização de task reescrita campo a campo (task_routes:17-28, user_routes:162-169) em vez de to_dict; validação de título/status/prioridade duplicada entre create e update e reimplementada em helpers.process_task_data (não usada); regex de e-mail repetida em vez de validate_email.
Impact: correções precisam ser feitas em N lugares e divergem (create e update já validam diferente).
Recommendation: única regra de atraso no model, validadores únicos reutilizados por create/update (PB-12).

### F12 [MEDIUM] Validação de entrada fraca gerando 500 (AP-16)
File: routes/task_routes.py:113, 167, 182, 260-264
File: routes/user_routes.py:102-103, 124-125
File: routes/report_routes.py:180, 196-202
Description: priority "alta" em POST/PUT /tasks gera TypeError na comparação < 1 (500); title null no PUT gera TypeError em len(); /tasks/search?priority=x gera ValueError em int(); PUT /categories sem corpo JSON gera TypeError em 'name' in None; nome de usuário/categoria pode virar vazio no update, active aceita qualquer tipo e color não é validado (is_valid_color existe e não é usado).
Impact: entradas inválidas viram 500 em vez de 400 e dados inconsistentes são persistidos.
Recommendation: validar tipo/formato em validadores centralizados e responder 400 (PB-12).

### F13 [MEDIUM] Tratamento de erro engolido e sem handler central (AP-17)
File: routes/task_routes.py:62, 137, 204, 236
File: routes/user_routes.py:87-90, 130, 149
File: routes/report_routes.py:186, 207, 221
File: utils/helpers.py:46, 49, 88
Description: 12 blocos `except:` sem tipo e try/except repetido em cada handler; GET /tasks engole qualquer exceção e responde 'Erro interno'; não há @app.errorhandler.
Impact: bugs escondidos (captura até KeyboardInterrupt/SystemExit), respostas de erro inconsistentes e difíceis de diagnosticar.
Recommendation: exceções de domínio + error handlers centrais registrados na factory; capturar exceções específicas (PB-09).

### F14 [LOW] Magic numbers e strings (AP-18)
File: routes/task_routes.py:96, 99, 104, 110, 113, 177, 182
File: routes/user_routes.py:64, 71, 115, 120
File: routes/report_routes.py:24-28, 45, 129, 180
File: app.py:34
Description: limites de título (3/200), prioridade (1-5, <= 2 = alta), senha mínima 4, janela de 7 dias, cor '#000000', listas de status/roles inline e porta 5000; constantes equivalentes em utils/helpers.py:110-116 existem mas não são usadas.
Impact: regras espalhadas e fáceis de divergir.
Recommendation: constantes de domínio em um único módulo reutilizado (PB-12).

### F15 [LOW] Nomenclatura ruim (AP-19)
File: routes/report_routes.py:24-28
File: routes/task_routes.py:7
Description: variáveis numeradas p1..p5 para contagem por prioridade; imports agrupados em uma linha (json, os, sys, time); variáveis t/u/c/cat em blocos longos.
Impact: leitura e manutenção mais difíceis.
Recommendation: nomes descritivos e mapeamento prioridade→rótulo nomeado (PB-12).

### F16 [LOW] Código morto, imports e dependências não usados (AP-20)
File: app.py:7
File: routes/task_routes.py:7
File: routes/user_routes.py:6
File: routes/report_routes.py:7-8
File: models/task.py:3, 38-60
File: models/user.py:34-38
File: utils/helpers.py:3-7, 9-116
File: services/notification_service.py:1-48
File: requirements.txt:4-6
Description: imports os/sys/json/time/hashlib/math/format_date/calculate_percentage sem uso; Task.validate_status/validate_priority/is_overdue e User.is_admin nunca chamados; quase todo utils/helpers e todo NotificationService não são referenciados; marshmallow, requests e python-dotenv declarados e nunca importados.
Impact: ruído, falsa sensação de camadas e superfície de dependências maior.
Recommendation: remover ou reaproveitar (ao consolidar validações e config) e limpar o manifesto (PB-14).

### F17 [LOW] print como logging (AP-21)
File: routes/task_routes.py:149, 153, 219, 234
File: routes/user_routes.py:83, 89, 147
File: services/notification_service.py:21, 24
File: utils/helpers.py:39, 41
Description: eventos e erros de aplicação emitidos com print(...).
Impact: sem nível, sem timestamp padronizado, impossível filtrar/encaminhar logs.
Recommendation: módulo logging com logger por módulo (PB-14).

### F18 [LOW] APIs deprecated (Query.get e datetime.utcnow) (AP-22)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227
File: routes/user_routes.py:29, 94, 136, 155
File: routes/report_routes.py:105, 192, 213
File: models/task.py:15-16, 52
File: models/user.py:14
File: models/category.py:11
Description: Model.query.get(id) (legado no SQLAlchemy 2.x, emite LegacyAPIWarning) e datetime.utcnow() (DeprecationWarning desde Python 3.12) usados em rotas e defaults de colunas (além de task_routes:31,72,215,285; report_routes:35,42,45,71,133; user_routes:172).
Impact: warnings em runtime hoje e quebra quando as APIs forem removidas.
Recommendation: db.session.get(Model, id) e helper utcnow() baseado em datetime.now(timezone.utc) (PB-11).

## Deprecated APIs
| API usada | Local | Versão detectada | Substituir por |
|---|---|---|---|
| `Model.query.get(id)` | routes/task_routes.py:42 (+15 locais, ver F18) | Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.x | `db.session.get(Model, id)` |
| `datetime.utcnow()` | models/task.py:15 (+ver F18) | Python 3.14.4 | `datetime.now(timezone.utc)` |

## Architecture verdict
Current: Parcialmente em camadas — pastas existem, mas rotas concentram validação, regra e ORM; services/utils mortos
Target:  MVC — introduzir config + create_app, controllers/services por domínio e views (blueprints) finas, reaproveitando os models existentes

================================
Total: 18 findings
================================
```
