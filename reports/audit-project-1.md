# Audit Report — Projeto 1: code-smells-project (Python/Flask)

> Saída da Fase 2 da skill `/refactor-arch`, executada em `code-smells-project/` (Claude Code 2.1.284, Opus 5.5).

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-09-28

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 5

## Findings

### F01 [CRITICAL] SQL Injection em praticamente todas as queries (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-299
Description: get_produto_por_id, criar_produto, atualizar_produto, deletar_produto, get_usuario_por_id, login_usuario, criar_usuario, criar_pedido, get_pedidos_usuario, get_todos_pedidos, atualizar_status_pedido e buscar_produtos montam SQL concatenando valores do request ("... WHERE email = '" + email + "' AND senha = '" + senha + "'"; query += " AND (nome LIKE '%" + termo + "%' ...").
Impact: bypass de login com ' OR '1'='1, leitura/alteração/destruição arbitrária do banco via /produtos/busca?q=, POST /usuarios, POST /produtos etc.
Recommendation: usar queries parametrizadas com placeholders ? em todas as chamadas execute, inclusive a busca dinâmica (lista de condições + lista de parâmetros) (PB-02).

### F02 [CRITICAL] Endpoint de execução de SQL arbitrário e reset do banco sem autenticação (AP-05)
File: app.py:47-57, 59-78
Description: POST /admin/query executa cursor.execute(query) com o campo "sql" do body; POST /admin/reset-db apaga as 4 tabelas. Nenhuma verificação de identidade/permissão.
Impact: qualquer cliente anônimo lê a tabela usuarios (com senhas), altera dados ou apaga o banco inteiro.
Recommendation: remover a execução de SQL arbitrário; proteger rotas admin com autenticação por token de admin configurado via ambiente e desabilitá-las se o token não estiver configurado (PB-13).

### F03 [CRITICAL] Secret key hardcoded e exposta no /health (AP-01, AP-06)
File: app.py:7
File: controllers.py:285-289
Description: SECRET_KEY definida como literal "minha-chave-super-secreta-123" e devolvida no JSON de GET /health junto com db_path, debug e ambiente.
Impact: qualquer leitor do repositório ou cliente de /health obtém a chave de assinatura de sessão e detalhes de infraestrutura.
Recommendation: ler SECRET_KEY de variável de ambiente em config.py e remover secret_key/db_path/debug da resposta do health (PB-01, PB-06).

### F04 [CRITICAL] Senhas armazenadas e comparadas em texto puro (AP-04)
File: database.py:75-83
File: models.py:109-111, 126-129
Description: seed insere "admin123", "123456", "senha123" sem hash; criar_usuario grava a senha recebida como está; login_usuario compara senha dentro do SQL (WHERE email = ... AND senha = ...).
Impact: vazamento do loja.db (trivial via /admin/query) expõe todas as senhas em claro.
Recommendation: usar werkzeug.security.generate_password_hash / check_password_hash (já dependência do Flask) e migrar hashes no seed (PB-06).

### F05 [CRITICAL] Senhas devolvidas pela API (AP-06)
File: models.py:83, 99
File: controllers.py:128-144
Description: get_todos_usuarios e get_usuario_por_id serializam o campo "senha"; GET /usuarios e GET /usuarios/<id> retornam a senha de cada usuário.
Impact: qualquer cliente coleta credenciais de todos os usuários.
Recommendation: serializar usuário sem o campo senha (to_dict público) (PB-06).

### F06 [CRITICAL] God File de acesso a dados com múltiplos domínios e regra de negócio (AP-03)
File: models.py:1-314
File: app.py:1-88
Description: models.py (314 linhas) concentra SQL, serialização e regras de 4 domínios (produtos, usuários, pedidos, relatórios), incluindo validação de estoque (144-146) e faixas de desconto (256-262). app.py mistura config, registro de rotas, handlers admin com SQL cru (49-55, 66-76) e bootstrap.
Impact: impossível testar em isolamento; toda mudança toca os mesmos arquivos.
Recommendation: separar em models/ por entidade, services (regra), controllers (HTTP), routes (blueprints) e app factory (PB-03).

### F07 [HIGH] Regra de negócio e efeitos colaterais na camada HTTP/dados (AP-07)
File: controllers.py:43-54, 87-90, 205-210, 242-250
File: models.py:139-146, 256-262
Description: controllers validam faixas de preço/estoque/categoria e disparam "ENVIANDO EMAIL/SMS/PUSH" e "NOTIFICAÇÃO" inline; models.criar_pedido calcula total e checa estoque; relatorio_vendas aplica faixas de desconto (10%/5%/2%). O cancelamento anuncia "Devolver estoque" mas não devolve.
Impact: regras só testáveis via HTTP/banco; notificações acopladas ao handler; bug silencioso no estoque de pedidos cancelados.
Recommendation: mover validação e regras para services (produto_service, pedido_service, relatorio_service) e notificações para um serviço dedicado (PB-04).

### F08 [HIGH] Conexão SQLite global mutável compartilhada entre threads (AP-08)
File: database.py:4, 8-10
Description: db_connection = None no módulo, criada com global db_connection e check_same_thread=False, reutilizada por todas as requisições.
Impact: condições de corrida entre requisições concorrentes, transações misturadas, testes interdependentes.
Recommendation: conexão por requisição em flask.g, fechada em teardown_appcontext (PB-05).

### F09 [HIGH] Configuração insegura: debug ligado, CORS aberto (AP-10)
File: app.py:8-9, 88
File: controllers.py:286
Description: app.config["DEBUG"] = True e app.run(host="0.0.0.0", port=5000, debug=True) fixos; CORS(app) sem origens; "ambiente": "producao" literal.
Impact: debugger do Werkzeug exposto em todas as interfaces permite execução remota de código; qualquer origem consome a API.
Recommendation: ler DEBUG, HOST, PORT e CORS_ORIGINS de variáveis de ambiente com defaults seguros (PB-01).

### F10 [HIGH] Autenticação ausente — login não emite token (AP-12)
File: controllers.py:167-186
File: app.py:11-30
Description: /login apenas retorna os dados do usuário; nenhuma rota verifica identidade (nenhum decorator/middleware de auth no projeto), incluindo GET /usuarios e GET /relatorios/vendas.
Impact: qualquer um lista usuários, pedidos e faturamento.
Recommendation: introduzir decorator de auth para rotas administrativas; manter o contrato das rotas públicas e documentar (PB-13).

### F11 [HIGH] Acoplamento direto à infraestrutura sem injeção de dependência (AP-09)
File: models.py:1, 5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286
File: controllers.py:3, 266
File: app.py:4, 49, 66
Description: todas as camadas importam e chamam get_db() global diretamente; controllers e app acessam o banco sem passar por models.
Impact: impossível substituir o banco em testes; camadas se atravessam.
Recommendation: acesso a dados apenas pelos models via conexão da app context; controllers dependem de services (PB-05).

### F12 [MEDIUM] Queries N+1 na listagem de pedidos e contagens repetidas no relatório (AP-13)
File: models.py:186-199, 218-231, 239-254
Description: get_pedidos_usuario e get_todos_pedidos fazem 1 query por pedido (cursor2) e 1 por item (cursor3); relatorio_vendas faz 5 queries separadas (COUNT/SUM/COUNT por status).
Impact: latência cresce linearmente com pedidos × itens.
Recommendation: JOIN itens_pedido × produtos com IN (...) e agregação com GROUP BY status (PB-07).

### F13 [MEDIUM] Criação de pedido e exclusão de produto sem transação/integridade (AP-14)
File: models.py:148-168
File: models.py:65-70
Description: criar_pedido faz INSERT pedido + N INSERT itens + N UPDATE estoque sem rollback em caso de exceção; deletar_produto apaga produto sem tratar itens_pedido que o referenciam.
Impact: pedido sem itens / estoque inconsistente em falhas parciais; itens órfãos ("Desconhecido").
Recommendation: envolver em transação (with conn: / rollback) e decrementar estoque de forma atômica (estoque >= ?) (PB-10).

### F14 [MEDIUM] Tratamento de erro repetido que vaza detalhes internos (AP-17, AP-06)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
File: app.py:77-78
Description: 17 blocos except Exception as e: return jsonify({"erro": str(e)}), 500; nenhum @app.errorhandler central.
Impact: mensagens de exceção do SQLite (estrutura de tabelas) chegam ao cliente; código repetido.
Recommendation: error handler central com exceções de domínio (ValidationError, NotFound) e resposta genérica para 500 (PB-09).

### F15 [MEDIUM] Validação duplicada e fraca (AP-15, AP-16)
File: controllers.py:28-50, 72-90, 118-121, 169-171, 195-201, 239-240
Description: validação de criar_produto é copiada em atualizar_produto, mas o update não valida nome/categoria; preco < 0 com string gera TypeError → 500; float(preco_min) inválido → 500; login/atualizar_status chamam dados.get sem checar body nulo → 500; itens de pedido não validam produto_id/quantidade (quantidade negativa aumenta estoque).
Impact: regras divergentes entre create/update, 500 em entradas simples, manipulação de estoque.
Recommendation: validador único por entidade no service, com checagem de tipo e retorno 400 (PB-12).

### F16 [MEDIUM] Mapeamento row→dict duplicado (AP-15)
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 178-199, 211-231
Description: o dicionário de produto é reescrito campo a campo 3 vezes, o de usuário 2 vezes e o de pedido+itens 2 vezes (get_pedidos_usuario e get_todos_pedidos são idênticos exceto pelo WHERE).
Impact: alterar um campo exige editar vários lugares; divergências silenciosas.
Recommendation: funções de serialização únicas por entidade e query de pedidos compartilhada (PB-12).

### F17 [LOW] print usado como logging e como "notificação" (AP-21)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
File: app.py:56, 83-86
Description: eventos, erros e notificações são emitidos via print, incluindo e-mail do usuário em login.
Impact: sem níveis, sem destino configurável; dados pessoais no stdout.
Recommendation: módulo logging com logger por módulo (PB-14).

### F18 [LOW] Magic numbers / strings de domínio (AP-18)
File: controllers.py:47-52, 242
File: models.py:257-262
File: app.py:88
Description: categorias válidas, status válidos, limites de nome (2/200), faixas de desconto (10000/0.1, 5000/0.05, 1000/0.02) e porta 5000 como literais inline.
Impact: regras dispersas e difíceis de alterar; ajusto para LOW mesmo com regra financeira pois é consolidado junto de F07.
Recommendation: constantes nomeadas no módulo de domínio/config (PB-12).

### F19 [LOW] Imports não usados (AP-20)
File: database.py:2
File: models.py:2
Description: import os em database.py e import sqlite3 em models.py nunca são usados.
Impact: ruído e falsa dependência.
Recommendation: remover imports mortos (PB-14).

### F20 [LOW] Nomenclatura ruim — builtin sombreado e cursores numerados (AP-19)
File: controllers.py:14, 56, 64, 98
File: models.py:24, 187, 191, 219, 223
Description: parâmetro/variável id sombreia o builtin; cursor2/cursor3 numerados.
Impact: legibilidade reduzida.
Recommendation: nomes descritivos (produto_id, itens_cursor) (PB-12).

### F21 [LOW] Rota de health com contadores via SQL no controller (AP-07)
File: controllers.py:264-274
Description: health_check executa SELECT 1 e 3 COUNTs diretamente no controller.
Impact: controller acoplado ao schema.
Recommendation: mover contagens para model/service de health (PB-04).

## Deprecated APIs
Nenhuma API deprecated encontrada para Python 3.12 + Flask 3.1.1 (verificados utcnow, before_first_request, JSONEncoder/json_encoder, JSON_AS_ASCII, distutils, pkg_resources, imp).

## Architecture verdict
Current: Monolítica / sem camadas
Target:  MVC — separar models por entidade com SQL parametrizado, services com as regras de negócio, controllers finos em blueprints e app factory com config por ambiente e error handler central.

================================
Total: 21 findings
================================
```
