```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-09

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### F01 [CRITICAL] SQL Injection em todas as queries de models.py (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299
Description: todas as funções de models.py montam SQL concatenando valores: login_usuario faz `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`, criar_produto/atualizar_produto/criar_usuario concatenam nome, descricao, categoria, email e senha vindos do body, criar_pedido concatena `usuario_id` e `item["produto_id"]` sem checar tipo, e buscar_produtos faz `query += " AND (nome LIKE '%" + termo + "%' ..."` e `" AND categoria = '" + categoria + "'"` com valores da query string. Os ids de rota (`<int:id>`) chegam como int, mas são concatenados do mesmo jeito. Routes: POST /login, POST /usuarios, POST /produtos, PUT /produtos/<id>, GET /produtos/busca, POST /pedidos
Impact: um cliente anônimo entra como qualquer usuário (inclusive o admin) com `email = "admin@loja.com' --"`; lê tabelas inteiras (inclusive senhas) via `UNION SELECT` em GET /produtos/busca; grava valores arbitrários (por exemplo `tipo = 'admin'`) por POST /usuarios e POST /produtos; cria pedidos com total/estoque manipulados via `usuario_id`/`produto_id` em POST /pedidos.
Recommendation: reescrever todas as chamadas `execute` com placeholders `?` e parâmetros separados, incluindo as de id inteiro e a busca dinâmica (lista de cláusulas + lista de parâmetros, `LIKE ?` com `%termo%` no parâmetro). Validar tipos de `usuario_id`, `produto_id` e `quantidade` antes de chegar ao model (PB-02). Como o finding é CRITICAL, exigir credencial válida em POST /usuarios, POST /produtos, PUT /produtos/<id>, GET /produtos/busca e POST /pedidos (POST /login é a rota que emite a credencial e fica pública) (PB-13).

### F02 [CRITICAL] Endpoints administrativos, destrutivos e financeiros sem autenticação (AP-05)
File: app.py:47-57, 59-78
File: controllers.py:98-109, 257-262
Description: `reset_database` apaga as 4 tabelas e `executar_query` executa `cursor.execute(query)` com o SQL cru de `dados.get("sql")`, fazendo commit de qualquer instrução que não comece com SELECT. `deletar_produto` apaga produtos e `relatorio_vendas` devolve faturamento bruto/líquido. Nenhuma das quatro tem verificação de identidade ou de perfil. Routes: POST /admin/reset-db, POST /admin/query, DELETE /produtos/<id>, GET /relatorios/vendas
Impact: qualquer cliente anônimo apaga o banco inteiro, lê qualquer tabela (inclusive `usuarios.senha`), executa `UPDATE`/`DROP`/`INSERT` arbitrários, apaga produtos do catálogo e consulta o faturamento da loja.
Recommendation: exigir token válido de perfil `admin` (decorator `require_admin`) nas quatro rotas, com 401 sem credencial e 403 com credencial não-admin. Restringir POST /admin/query a uma única instrução SELECT executada em conexão somente leitura (`mode=ro`), rejeitando com 400 qualquer outra instrução, para que nem um admin consiga alterar ou destruir dados por essa rota. Mover o SQL dos handlers para um model administrativo (PB-13, PB-03).

### F03 [CRITICAL] Senhas armazenadas e comparadas em texto puro (AP-04)
File: database.py:75-83
File: models.py:109-111, 126-129
Description: o seed insere `("Admin", "admin@loja.com", "admin123", "admin")` e as demais senhas sem hash; `criar_usuario` grava `senha` do body como veio; `login_usuario` compara a senha no próprio SQL (`AND senha = '" + senha + "'`), o que só funciona com texto puro. Routes: POST /usuarios, POST /login
Impact: qualquer vazamento do banco (via F01, F02, F04 ou cópia do `loja.db`) entrega as senhas de todos os usuários em claro, reutilizáveis em outros serviços.
Recommendation: gravar `werkzeug.security.generate_password_hash(senha)` em POST /usuarios e no seed. Em POST /login, buscar o usuário só pelo e-mail e validar com `check_password_hash`. No boot, migrar para hash as linhas existentes que ainda estejam em texto puro (PB-06). POST /usuarios passa a exigir credencial (CRITICAL; ver F01); POST /login é a rota que emite a credencial.

### F04 [CRITICAL] Exposição de senhas e configuração em respostas JSON (AP-06)
File: models.py:79-86, 95-102
File: controllers.py:276-290
Description: `get_todos_usuarios` e `get_usuario_por_id` serializam `"senha": row["senha"]`; `health_check` devolve `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True` e `"ambiente": "producao"`. Nenhuma das rotas exige autenticação. Routes: GET /usuarios, GET /usuarios/<id>, GET /health
Impact: qualquer cliente anônimo obtém e-mail e senha de todos os usuários (GET /usuarios) ou de um usuário específico (GET /usuarios/<id>), e a SECRET_KEY da aplicação mais detalhes de infraestrutura (GET /health).
Recommendation: remover `senha` de toda serialização de usuário, com um único `usuario_to_dict` sem o campo. Remover `secret_key`, `db_path`, `debug` e `ambiente` do health (PB-06). Exigir credencial: GET /usuarios só admin; GET /usuarios/<id> só o próprio usuário ou admin; GET /health qualquer usuário autenticado (PB-13).

### F05 [CRITICAL] SECRET_KEY hardcoded no código (AP-01)
File: app.py:7
File: controllers.py:289
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está escrita como literal e a mesma string é repetida no JSON de `health_check`. Routes: GET /health
Impact: qualquer leitor do repositório ou cliente de GET /health conhece a chave usada para assinar sessões e tokens e pode forjá-los; trocar a chave exige alterar código e fazer deploy.
Recommendation: ler `SECRET_KEY` de variável de ambiente num módulo `config/settings.py`, gerando uma chave aleatória (`secrets.token_hex`) com aviso no log quando ela não estiver definida. Documentar a variável em `.env.example` e remover a chave da resposta de GET /health, que passa a exigir credencial (PB-01, PB-06, PB-13).

### F06 [CRITICAL] Arquivos-deus sem separação de camadas (AP-03)
File: app.py:1-88
File: controllers.py:1-292
File: models.py:1-314
Description: app.py mistura config, CORS, registro de rotas, handlers administrativos com SQL (`reset_database`, `executar_query`) e bootstrap. controllers.py concentra validação, regra, notificações e SQL direto (`health_check`, linhas 264-274) de 5 domínios. models.py (314 linhas) junta SQL, serialização e regra de negócio de produtos, usuários, pedidos e relatórios. Routes: nenhuma
Impact: nenhuma parte é testável isoladamente; qualquer mudança em um domínio mexe nos mesmos arquivos dos outros; não há ponto único para auth, erros ou config.
Recommendation: dividir em `src/config`, `src/database`, `src/models/<dominio>`, `src/services/<dominio>`, `src/controllers/<dominio>`, `src/views/<dominio>_routes.py` (Blueprints) e `src/middlewares`, com `create_app()` como composition root. O app.py da raiz vira só o entry point (PB-03).

### F07 [HIGH] Autenticação inexistente: login não emite credencial e nenhuma rota verifica identidade (AP-12)
File: controllers.py:167-183
File: app.py:11-30
Description: `login` só devolve os dados do usuário (sem token nem sessão) e nenhuma rota tem decorator ou middleware de auth. Rotas que listam dados de todos os clientes, alteram catálogo e pedidos ou criam pedidos para qualquer `usuario_id` são públicas. Routes: POST /produtos, PUT /produtos/<id>, GET /usuarios, GET /usuarios/<id>, GET /pedidos, GET /pedidos/usuario/<id>, POST /pedidos, PUT /pedidos/<id>/status
Impact: qualquer cliente anônimo lista todos os usuários e todos os pedidos (com itens e valores) de qualquer cliente, cria e altera produtos, muda o status de qualquer pedido (inclusive aprovar ou cancelar) e cria pedidos em nome de qualquer usuário, debitando o estoque.
Recommendation: POST /login passa a emitir um token assinado com expiração (`itsdangerous.URLSafeTimedSerializer` com a SECRET_KEY, que já vem com o Flask), validado por `require_auth` e `require_admin` (header `Authorization: Bearer`). Somente admin: POST /produtos, PUT /produtos/<id>, GET /usuarios, GET /pedidos, PUT /pedidos/<id>/status. Próprio usuário ou admin: GET /usuarios/<id>, GET /pedidos/usuario/<id> e POST /pedidos (`usuario_id` do body precisa ser o do token, salvo admin) (PB-13).

### F08 [HIGH] Configuração insegura: debug ligado fixo e CORS aberto (AP-10)
File: app.py:8, 9, 88
File: controllers.py:286, 288
Description: `app.config["DEBUG"] = True`, `app.run(host="0.0.0.0", port=5000, debug=True)` e `CORS(app)` sem lista de origens estão fixos no código; health anuncia `"ambiente": "producao"` com `"debug": True`. Routes: todas as rotas (CORS `*` em todas; o debugger do Werkzeug aparece em qualquer exceção não tratada)
Impact: com o servidor em 0.0.0.0 e o debugger interativo ativo, qualquer erro não tratado expõe stack trace e um console Python (protegido só por PIN) a quem estiver na rede; CORS `*` deixa qualquer site chamar a API pelo navegador da vítima.
Recommendation: ler `DEBUG` (padrão `false`), `HOST`, `PORT` e `CORS_ORIGINS` de variáveis de ambiente em config/settings. Aplicar `CORS(app, origins=CORS_ORIGINS)` sem curinga por padrão e remover os campos de ambiente do health (PB-01).

### F09 [HIGH] Conexão SQLite global e mutável compartilhada entre threads (AP-08)
File: database.py:4-11
Description: `db_connection = None` no módulo, `global db_connection` em `get_db()` e `sqlite3.connect(db_path, check_same_thread=False)`: uma única conexão é criada sob demanda e compartilhada por todas as requisições do servidor multi-thread do Flask. Routes: todas as rotas que acessam o banco (todas exceto GET /)
Impact: requisições concorrentes usam o mesmo objeto de conexão e transação; um commit ou erro de uma requisição afeta a outra, gerando dados inconsistentes e erros intermitentes; schema e seed rodam como efeito colateral da primeira chamada.
Recommendation: abrir uma conexão por requisição (`flask.g` + `teardown_appcontext` fechando a conexão), sem `check_same_thread=False`, e mover schema + seed para uma função `init_db()` chamada uma vez em `create_app()` (PB-05).

### F10 [HIGH] Acoplamento direto à infraestrutura de banco (AP-09)
File: models.py:1, 5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286
File: controllers.py:3, 266
File: app.py:4, 49, 66
Description: cada função de models chama o `get_db()` global; controllers.py e app.py importam `database` direto para rodar SQL (`health_check`, `reset_database`, `executar_query`), passando por cima da camada de models. Routes: nenhuma
Impact: impossível testar models e controllers com um banco fake ou de teste; trocar o banco ou a forma de conexão exige editar todas as camadas.
Recommendation: concentrar o acesso a conexão em `src/database/connection.py` (`get_connection()` por requisição). Os models recebem/obtêm a conexão por esse único ponto, e controllers e views nunca importam `database`: o SQL de health e admin vai para models próprios (PB-05).

### F11 [HIGH] Regra de negócio e efeitos colaterais na camada HTTP e no acesso a dados (AP-07)
File: controllers.py:24-62, 188-220, 237-255
File: models.py:133-169, 235-273
Description: `criar_produto` valida e aplica regras (faixa de nome, categorias) no controller; `criar_pedido` e `atualizar_status_pedido` disparam "notificações" (`print("ENVIANDO EMAIL...")`, SMS, push) dentro do handler; `models.criar_pedido` decide estoque e total e `models.relatorio_vendas` calcula as faixas de desconto (10%/5%/2%) dentro da camada de dados. Routes: nenhuma (impacto estrutural)
Impact: regras de preço, estoque e desconto só podem ser testadas via HTTP ou com banco real; os efeitos colaterais ficam presos ao handler e não podem ser trocados por um serviço real de notificação.
Recommendation: criar services (`produto_service`, `pedido_service`, `relatorio_service`) com as regras e um `notification_service` para os efeitos colaterais. Controllers só traduzem HTTP ↔ service e models só fazem SQL e mapeamento (PB-04).

### F12 [MEDIUM] Queries N+1 em pedidos e contagens repetidas no relatório (AP-13)
File: models.py:174-201, 206-233, 239-254
Description: `get_pedidos_usuario` e `get_todos_pedidos` fazem 1 query de pedidos, mais 1 (`cursor2`) por pedido para os itens, mais 1 (`cursor3`) por item para o nome do produto; `relatorio_vendas` faz 5 queries separadas (COUNT, SUM e 3 COUNT por status). Routes: GET /pedidos, GET /pedidos/usuario/<id>, GET /relatorios/vendas
Impact: o número de queries cresce com pedidos × itens; com muitos pedidos as listagens ficam lentas e seguram a conexão compartilhada.
Recommendation: buscar itens com `JOIN produtos` para todos os pedidos de uma vez (`WHERE pedido_id IN (...)`) e agrupar em memória; calcular o relatório numa única query com `COUNT`, `SUM` e `SUM(CASE WHEN status = ? ...)` (PB-07).

### F13 [MEDIUM] Criação de pedido e exclusões sem transação nem integridade referencial (AP-14)
File: models.py:133-169, 65-70
File: database.py:36-53
File: app.py:51-55
Description: `criar_pedido` checa o estoque (linha 144) e só depois insere o pedido, os itens e faz `UPDATE produtos SET estoque = estoque - ...` em vários `execute` sem rollback em caso de falha. `deletar_produto` apaga produtos referenciados por `itens_pedido`, que viram "Desconhecido". O schema não declara `FOREIGN KEY`. Routes: POST /pedidos, DELETE /produtos/<id>, POST /admin/reset-db
Impact: falha no meio do loop deixa pedido sem itens ou estoque debitado pela metade; dois pedidos simultâneos podem passar na checagem e deixar estoque negativo; excluir um produto vendido corrompe o histórico de pedidos.
Recommendation: executar `criar_pedido` e o reset dentro de uma transação (`with conn:`), com débito condicional `UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?` e rollback se nenhuma linha for afetada. Declarar `FOREIGN KEY` no schema com `PRAGMA foreign_keys = ON`, e em DELETE /produtos/<id> responder 409 quando o produto tiver itens de pedido (PB-10).

### F14 [MEDIUM] Validação e mapeamento duplicados (AP-15)
File: controllers.py:28-50, 72-90
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233
Description: as validações de `criar_produto` e `atualizar_produto` são cópias, mas a do update não checa tamanho do nome nem categoria. O mapeamento row→dict de produto aparece 3 vezes e o de usuário 2 vezes; `get_pedidos_usuario` e `get_todos_pedidos` são quase idênticas. Routes: PUT /produtos/<id>
Impact: as cópias divergem: PUT /produtos/<id> aceita nome de 1 caractere e categoria inexistente, que POST /produtos rejeita; corrigir um bug exige lembrar de todas as cópias.
Recommendation: um único validador de produto usado por create e update, um único `produto_to_dict`/`usuario_to_dict` e uma única função de listagem de pedidos com filtro opcional por usuário (PB-12).

### F15 [MEDIUM] Validação de entrada ausente ou fraca (AP-16)
File: controllers.py:43-46, 118-121, 153-158, 169-171, 195-201, 239-245
File: models.py:144-146
File: database.py:27-34
Description: `preco`/`estoque` não têm tipo verificado (string → TypeError → 500); `float(preco_min)` sem tratamento (→ 500); `login` e `atualizar_status_pedido` usam `request.get_json().get(...)` sem checar None (→ 500); `criar_pedido` não valida `usuario_id`, `produto_id` nem `quantidade`, e quantidade negativa passa por `produto["estoque"] < item["quantidade"]`; e-mail sem formato nem unicidade (sem `UNIQUE`); PUT de status em pedido inexistente devolve 200. Routes: POST /produtos, PUT /produtos/<id>, GET /produtos/busca, POST /usuarios, POST /login, POST /pedidos, PUT /pedidos/<id>/status
Impact: entradas malformadas viram 500 em vez de 400; um pedido com `quantidade: -5` aumenta o estoque e gera total negativo; dá para cadastrar o mesmo e-mail várias vezes (o login passa a escolher um registro arbitrário); atualizar um pedido inexistente "funciona".
Recommendation: validar tipos e faixas em todas essas rotas (números não-booleanos ≥ 0, `quantidade` inteira > 0, ids inteiros positivos, e-mail com formato válido, body JSON obrigatório), respondendo 400. Responder 409 a e-mail duplicado (checagem no service + índice `UNIQUE`) e 404 em PUT /pedidos/<id>/status para pedido inexistente (PB-12).

### F16 [MEDIUM] Tratamento de erro repetido que vaza detalhes internos (AP-17)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
File: app.py:77-78
Description: 16 handlers repetem `except Exception as e: return jsonify({"erro": str(e)}), 500` e `executar_query` devolve `str(e)` da exceção do SQLite; não existe `@app.errorhandler` central. Routes: GET /produtos, GET /produtos/<id>, POST /produtos, PUT /produtos/<id>, DELETE /produtos/<id>, GET /produtos/busca, GET /usuarios, GET /usuarios/<id>, POST /usuarios, POST /login, POST /pedidos, GET /pedidos, GET /pedidos/usuario/<id>, PUT /pedidos/<id>/status, GET /relatorios/vendas, GET /health, POST /admin/query
Impact: mensagens de exceção do Python e do SQLite (nomes de tabelas, colunas, trechos de SQL) chegam ao cliente e ajudam a explorar F01; o mesmo bloco repetido 16 vezes esconde erros de programação como se fossem erros de negócio.
Recommendation: criar exceções de domínio (`ValidationError` 400, `NotFoundError` 404, `ConflictError` 409, `AuthError` 401/403) e um error handler central que as converte em `{"erro": ...}`. Exceções inesperadas são logadas com stack trace e respondidas com 500 e mensagem genérica; remover os try/except dos handlers (PB-09).

### F17 [LOW] Magic numbers e strings de domínio (AP-18)
File: controllers.py:47-50, 52, 242, 285
File: models.py:247-262
File: app.py:36, 88
Description: limites de nome `< 2`/`> 200`, lista de categorias e lista de status inline; faixas de desconto `10000/0.1`, `5000/0.05`, `1000/0.02`; status `'pendente'`, `'aprovado'`, `'cancelado'` soltos; versão `"1.0.0"` duplicada; porta `5000` fixa. Routes: nenhuma
Impact: mudar uma regra (nova categoria, nova faixa de desconto) exige caçar literais em vários arquivos, com risco de divergência.
Recommendation: concentrar em `config/constants.py` (`CATEGORIAS_VALIDAS`, `STATUS_PEDIDO`, `FAIXAS_DESCONTO`, `NOME_MIN/MAX`, `API_VERSION`) e porta via config (PB-12).

### F18 [LOW] Nomenclatura ruim (AP-19)
File: controllers.py:14, 56, 64, 98, 136, 160
File: models.py:24, 54, 65, 89, 187-193, 219-225
Description: parâmetros e variáveis `id` sombreiam o builtin; cursores numerados `cursor2`/`cursor3` e abreviação `prod`. Routes: nenhuma
Impact: leitura mais difícil e risco de bug ao usar `id()` dentro dessas funções.
Recommendation: renomear para `produto_id`, `usuario_id`, `novo_id`, e eliminar `cursor2`/`cursor3` com a query única de F12 (PB-12).

### F19 [LOW] Imports não usados (AP-20)
File: models.py:2
File: database.py:2
Description: `import sqlite3` em models.py e `import os` em database.py nunca são referenciados. Routes: nenhuma
Impact: ruído e falsa impressão de dependência.
Recommendation: remover os imports mortos na reorganização (PB-14).

### F20 [LOW] print usado como logging e notificação (AP-21)
File: app.py:56, 83-86
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: eventos, erros e "notificações" (EMAIL/SMS/PUSH) saem via `print`, inclusive o e-mail do usuário em logins e cadastros (161, 179, 182). Routes: nenhuma
Impact: sem nível, timestamp ou destino configurável; erros se misturam com stdout; e-mails (dado pessoal) ficam em log sem controle.
Recommendation: usar `logging.getLogger(__name__)` com níveis, mover notificações para `notification_service` e não registrar o e-mail em claro nos logs de login (PB-14).

## Deprecated APIs
Nenhuma API deprecated encontrada para Python 3.14 + Flask 3.1.1 + flask-cors 5.0.1 + sqlite3 (verificados: `datetime.utcnow`, `before_first_request`, `JSONEncoder`/`json_encoder`, `imp`, `distutils`, `pkg_resources`, adaptadores padrão de datetime do sqlite3).

## Architecture verdict
Current: Monolítica / sem camadas — rotas, SQL e regra de negócio misturados em 4 arquivos planos
Target:  MVC — separar config, conexão por requisição, models com SQL parametrizado, services com regra, controllers finos e Blueprints, com auth e error handler centrais em `create_app()`.

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
