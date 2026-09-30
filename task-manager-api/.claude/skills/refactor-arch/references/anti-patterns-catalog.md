# Referência — Catálogo de Anti-patterns (Fase 2)

Cada entrada traz: **severidade padrão**, **o que é**, **sinais de detecção** (acionáveis, com regex para `grep -nE`), **falsos positivos** a descartar e o **padrão de correção** no playbook (`PB-xx`).

## Escala de severidade

| Severidade | Quando usar |
|---|---|
| **CRITICAL** | Falha grave de segurança ou arquitetura: expõe dados/segredos, permite injeção, ou viola completamente a separação de responsabilidades (God Class com banco + regra + roteamento). |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes: regra de negócio no controller/rota, acoplamento sem DI, estado global mutável, config insegura. |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, validação ausente/duplicada, falta de transação, tratamento de erro inadequado. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, código morto, logging com print, APIs deprecated sem impacto imediato. |

Ajuste a severidade **só com justificativa escrita no finding** (ex.: rota destrutiva sem auth em app interno → mantém CRITICAL; magic number que define regra financeira → pode subir para MEDIUM).

## Índice

| ID | Anti-pattern | Severidade | Playbook |
|---|---|---|---|
| AP-01 | Credenciais / segredos hardcoded | CRITICAL | PB-01 |
| AP-02 | SQL Injection (query por concatenação/interpolação) | CRITICAL | PB-02 |
| AP-03 | God Class / God File | CRITICAL | PB-03 |
| AP-04 | Armazenamento inseguro de senha / criptografia fraca | CRITICAL | PB-06 |
| AP-05 | Endpoint sensível/administrativo sem autenticação | CRITICAL | PB-13 |
| AP-06 | Exposição de dados sensíveis (resposta, log, health) | CRITICAL | PB-06 |
| AP-07 | Regra de negócio na camada HTTP (Fat Route/Controller) | HIGH | PB-04 |
| AP-08 | Estado global mutável | HIGH | PB-05 |
| AP-09 | Acoplamento forte sem injeção de dependência | HIGH | PB-05 |
| AP-10 | Configuração insegura (debug em produção, CORS aberto) | HIGH | PB-01 |
| AP-11 | Callback hell / fluxo assíncrono aninhado | HIGH | PB-08 |
| AP-12 | Autenticação falsa ou ausente | HIGH | PB-13 |
| AP-13 | Queries N+1 | MEDIUM | PB-07 |
| AP-14 | Operação multi-etapa sem transação / integridade referencial | MEDIUM | PB-10 |
| AP-15 | Lógica ou validação duplicada | MEDIUM | PB-12 |
| AP-16 | Validação de entrada ausente ou fraca | MEDIUM | PB-12 |
| AP-17 | Tratamento de erro espalhado, engolido ou vazando detalhes | MEDIUM | PB-09 |
| AP-18 | Magic numbers / strings | LOW | PB-12 |
| AP-19 | Nomenclatura ruim | LOW | PB-12 |
| AP-20 | Código morto / imports e dependências não usados | LOW | PB-14 |
| AP-21 | `print`/`console.log` como logging | LOW | PB-14 |
| AP-22 | APIs deprecated | LOW (MEDIUM se já removida na versão em uso ou na próxima major) | PB-11 |

---

## CRITICAL

### AP-01 — Credenciais / segredos hardcoded
**O que é:** senha, chave de API, secret de sessão, token ou string de conexão com senha escritos como literal no código.
**Sinais:**
- `grep -rnEi "(secret|passw(or)?d|pwd|pass|key|token|credential|senha|chave)\w*[\"']?\]?\s*[:=]\s*[\"'][^\"']{4,}[\"']"` — cobre `SECRET_KEY = '...'`, `app.config["SECRET_KEY"] = "..."`, `paymentGatewayKey: "..."`, `self.email_password = '...'` (nomes em inglês e português, snake e camelCase)
- Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox[bp]-`
- URIs com credenciais: `://[^/\s:]+:[^@\s]+@`
- Objetos `config = { dbPass: "...", ... }` exportados de um módulo.
**Falsos positivos:** leitura de env (`os.environ[...]`, `process.env.X`), placeholders em `.env.example`, **dados de seed** de demonstração (esses entram em AP-04 se forem senhas em texto puro).
**Impacto:** qualquer pessoa com acesso ao repositório obtém os segredos; rotação exige deploy.

### AP-02 — SQL Injection
**O que é:** SQL montado com dados externos via concatenação/interpolação em vez de parâmetros.
**Sinais:**
- Python: `execute\(\s*["'].*["']\s*\+`, `execute\(f["']`, `execute\(.*%\s*\(`, `execute\(.*\.format\(`, `query\s*\+=\s*["'].*["']\s*\+`
- JS: `(query|run|get|all|exec)\(\s*` seguido de template literal com `${` ou `"...' +`
- Palavras SQL (`SELECT|INSERT|UPDATE|DELETE|WHERE`) na mesma linha que `+ str(` / `+ variavel +` / `${`.
- Endpoint que executa SQL recebido do cliente (`execute(dados["sql"])`) — CRITICAL por si só.
**Falsos positivos:** placeholders `?`, `%s`, `:nome`, `$1` com parâmetros separados; ORMs com filtros (`filter_by`, `.where(Model.x == y)`); `LIKE` com parâmetro.
**Impacto:** leitura/alteração/destruição arbitrária do banco, bypass de login (`' OR '1'='1`).

### AP-03 — God Class / God File
**O que é:** um único arquivo/classe acumula responsabilidades de camadas diferentes (roteamento **e** acesso a dados **e** regra de negócio) ou de vários domínios.
**Sinais:**
- Mesmo arquivo contém registro de rotas (`app.get(`, `@app.route`, `add_url_rule`) **e** SQL/ORM (`execute(`, `db.run(`, `.query.`).
- Classe com métodos `initDb`/`setupRoutes`/handlers de negócio juntos (ex.: `AppManager`, `Manager`, `Utils` gigantes).
- Arquivo > ~250 linhas com funções de ≥ 3 entidades de domínio diferentes (ex.: produtos, usuários, pedidos, relatórios).
- Função/método > ~50 linhas misturando validação, persistência e formatação.
**Falsos positivos:** composition root que só **registra** rotas importadas; arquivo de models grande mas coeso a uma entidade.
**Impacto:** impossível testar em isolamento; qualquer mudança afeta tudo; conflitos de merge constantes.

### AP-04 — Senha em texto puro / criptografia fraca
**O que é:** senha salva sem hash, com hash rápido/quebrado (MD5, SHA1 sem salt) ou "criptografia" caseira (base64, loops, substring).
**Sinais:**
- `hashlib\.(md5|sha1)\(`, `createHash\(['"](md5|sha1)['"]\)`
- `base64` / `Buffer.from(.*).toString\('base64'\)` aplicado a senha; funções com nomes como `badCrypto`, `encrypt` sem biblioteca
- `INSERT INTO usuarios? .* senha|password` com valor vindo direto do request/seed sem hash
- Comparação `WHERE email = ? AND senha = ?` (senha comparada no SQL ⇒ texto puro)
- Senha padrão quando ausente: `pwd || "123456"`
**Falsos positivos:** `bcrypt`, `argon2`, `scrypt`, `pbkdf2`, `werkzeug.security.generate_password_hash`.
**Impacto:** vazamento do banco = vazamento de todas as senhas (e de contas em outros serviços, por reuso).

### AP-05 — Endpoint sensível/administrativo sem autenticação
**O que é:** rotas que apagam dados, executam comandos/SQL, expõem relatórios financeiros ou administram usuários sem qualquer verificação de identidade/permissão.
**Sinais:**
- Paths com `admin`, `reset`, `query`, `exec`, `debug`, `financial`, `report` sem decorator/middleware de auth.
- Handlers `DELETE` de usuários/recursos sem checagem.
- `cursor.execute(<valor do request>)`.
**Impacto:** qualquer cliente anônimo destrói ou lê todo o sistema.

### AP-06 — Exposição de dados sensíveis
**O que é:** dado sensível devolvido em respostas ou gravado em logs.
**Sinais:**
- Serialização (`to_dict`, `jsonify`, `res.json`) incluindo `password`, `senha`, `pass`, `hash`, `secret_key`, `token`.
- Health/debug endpoints retornando config (`"secret_key":`, `"db_path":`, `"debug":`).
- Logs com PAN/cartão, senha ou chave: `console.log(.*(card|cc|cartao|pwd|senha|key))`, `print(.*senha)`.
- `return jsonify({"erro": str(e)})` com exceções de banco (vaza SQL/estrutura) — ver também AP-17.
**Impacto:** vazamento de credenciais, violação de LGPD/PCI-DSS.

---

## HIGH

### AP-07 — Regra de negócio na camada HTTP (Fat Route / Fat Controller)
**O que é:** handler de rota/controller que calcula, agrega, decide regras de domínio ou faz várias queries, em vez de delegar.
**Sinais:**
- Handler com > ~30 linhas, ou que contém ao mesmo tempo `request`/`req` **e** queries/ORM **e** cálculos (`+=`, `round(`, percentuais, descontos, contagens por status).
- Regras de domínio (faixas de desconto, aprovação de pagamento, cálculo de atraso) dentro de rota ou de model de acesso a dados.
- Efeitos colaterais de infraestrutura no handler: envio de e-mail/SMS/push, escrita de auditoria.
**Impacto:** regra só testável via HTTP; duplicação entre endpoints; viola SRP.

### AP-08 — Estado global mutável
**O que é:** variáveis de módulo alteradas em runtime e compartilhadas entre requisições.
**Sinais:**
- Python: `^\w+\s*=\s*(None|\{\}|\[\]|0)` no topo do módulo + `global \w+` dentro de funções.
- JS: `^let \w+\s*=` no topo do módulo, objetos exportados e mutados (`globalCache[key] = ...`).
- Conexão de banco global única criada preguiçosamente (`db_connection = None` … `global db_connection`), especialmente com `check_same_thread=False`.
- Listas em instância singleton acumulando dados indefinidamente (`self.notifications.append`).
**Impacto:** condições de corrida, vazamento de memória, testes interdependentes, impossibilidade de escalar horizontalmente.

### AP-09 — Acoplamento forte sem injeção de dependência
**O que é:** camadas instanciam/importam diretamente infraestrutura concreta (banco, SMTP, gateway) em vez de recebê-la.
**Sinais:**
- `get_db()` global chamado dentro de models/controllers; `new sqlite3.Database(` dentro de classe de domínio.
- `smtplib.SMTP(`, `requests.post(` dentro de model/route.
- Importação circular ou de "mão dupla" (controller importa `database` e `models`, e `app` importa `database` para rotas admin).
**Impacto:** impossível substituir por fakes em teste; troca de infraestrutura exige alterar regra de negócio.

### AP-10 — Configuração insegura
**O que é:** modo debug ou opções permissivas hardcoded, ativas independentemente do ambiente.
**Sinais:** `debug=True`, `DEBUG\s*=\s*True`, `app.run\(.*debug=True`, `host=['"]0\.0\.0\.0['"]` junto com debug, `CORS\(app\)` sem origens, `"ambiente": "producao"` literal.
**Impacto:** o debugger do Werkzeug permite execução remota de código; CORS aberto expõe a API a qualquer origem.

### AP-11 — Callback hell / fluxo assíncrono aninhado
**O que é:** operações assíncronas encadeadas por callbacks aninhados (≥ 3 níveis), com contadores manuais de pendências.
**Sinais:** `function(err` / `(err, ` aninhados em ≥ 3 níveis; contadores tipo `pending--; if (pending === 0)`; `const self = this` para escapar de `function`.
**Impacto:** erros não propagam, respostas duplicadas/ausentes, lógica ilegível e intestável.

### AP-12 — Autenticação falsa ou ausente
**O que é:** login que emite token previsível/não assinado, ou API sem nenhuma verificação de token nas rotas protegidas.
**Sinais:** `'fake-jwt'`, `token = 'x' + str(user.id)`, login que retorna o usuário sem token/sessão, nenhum decorator/middleware de auth no projeto.
**Impacto:** qualquer um forja identidade.

---

## MEDIUM

### AP-13 — Queries N+1
**O que é:** uma query para a lista e mais uma (ou mais) por item.
**Sinais:**
- Chamada de banco/ORM **dentro** de `for`/`forEach`/`map`: `for .*:\n\s+.*(execute|query\.|\.get\(|filter_by|db\.(get|all|run))`.
- Acesso a relacionamento lazy dentro de loop (`len(u.tasks)`, `t.user.name`).
- Contagens repetidas por categoria/status: várias `.count()` / `SELECT COUNT(*) ... WHERE status = '...'` em sequência (MEDIUM se ≥ 4).
**Correção:** `JOIN`, `IN (...)`, eager loading (`joinedload`/`selectinload`), `GROUP BY`.

### AP-14 — Operação multi-etapa sem transação / sem integridade referencial
**Sinais:** várias escritas (`INSERT`/`UPDATE`) sequenciais para uma operação de negócio sem `BEGIN/COMMIT/ROLLBACK` ou `with conn:`; `DELETE` de entidade pai sem tratar filhos (órfãos); `return` de erro no meio de um loop após já ter escrito.
**Impacto:** dados inconsistentes em falhas parciais (pedido sem itens, estoque errado, pagamentos órfãos).

### AP-15 — Lógica ou validação duplicada
**Sinais:** blocos idênticos/quase idênticos em ≥ 2 lugares (validação de create vs. update; cálculo de "atrasado"; mapeamento row→dict repetido campo a campo); utilitários existentes que **não são usados** enquanto a lógica é reimplementada inline.
**Dica:** compare funções com nomes simétricos (`criar_x`/`atualizar_x`, `create`/`update`) e procure a mesma condição com `grep -n "<condição>" -r`.

### AP-16 — Validação de entrada ausente ou fraca
**Sinais:** uso de campos do body sem checar tipo/formato (`priority < 1` com string → `TypeError` 500); `int(request.args[...])` sem tratamento; só checagem de presença (`if (!a || !b)`); update que aceita valores que o create rejeita.

### AP-17 — Tratamento de erro espalhado, engolido ou vazando detalhes
**Sinais:**
- `except:` sem tipo (Python) — `grep -nE "except\s*:"`.
- `try/except Exception as e: return jsonify({"erro": str(e)}), 500` repetido em todo handler.
- Callbacks que ignoram `err` (`(err, rows) => { rows.length ...`) ou respondem sempre sucesso.
- Ausência de handler central (`@app.errorhandler`, middleware `(err, req, res, next)`).

---

## LOW

### AP-18 — Magic numbers / strings
**Sinais:** literais numéricos com significado de negócio (`10000`, `0.1`, `<= 2`, `len(x) < 4`), listas de valores válidos inline (`['pending', 'done', ...]`), status como strings soltas repetidas, portas fixas.
**Correção:** constantes nomeadas / enums no módulo de domínio ou config.

### AP-19 — Nomenclatura ruim
**Sinais:** variáveis de 1-3 letras sem significado fora de loops curtos (`u, e, p, cid, cc`); nomes numerados (`cursor2`, `cursor3`, `p1..p5`); parâmetros que sombreiam builtins (`id`, `type`, `list`); nomes enganosos (`badCrypto`, `utils` genérico); campos de API abreviados (`usr`, `eml`).

### AP-20 — Código morto / imports e dependências não usados
**Sinais:** imports sem uso (compare cada nome importado com `grep -c`); variáveis/exports nunca lidos; serviços/utilitários/constantes definidos e não referenciados; dependências no manifesto nunca importadas.

### AP-21 — `print` / `console.log` como logging
**Sinais:** `print(` / `console.log(` em código de aplicação (não scripts de seed/CLI) para eventos, erros ou "notificações".
**Correção:** módulo `logging` / logger estruturado com níveis.

### AP-22 — APIs deprecated
**O que é:** uso de APIs obsoletas (deprecated ou removidas) na versão da linguagem/framework detectada na Fase 1. Sempre recomende o **equivalente moderno**.
**Severidade:** LOW por padrão; **MEDIUM** se já emite warning na versão instalada e será removida na próxima major; **HIGH** se a API já foi removida (quebra no upgrade/boot).

| Ecossistema | Deprecated (sinal para grep) | Equivalente moderno |
|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp(` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| Python | `import imp`, `distutils`, `pkg_resources`, `asyncio.get_event_loop()` fora de loop | `importlib`, `setuptools`/`packaging`, `importlib.metadata`, `asyncio.run()` |
| SQLAlchemy ≥ 2.0 / Flask-SQLAlchemy ≥ 3 | `Model.query.get(id)`, `session.query(X).get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy ≥ 2.0 | `engine.execute(`, `Model.query.filter(...)` em código novo (estilo legado 1.x) | `with engine.connect() as c: c.execute(text(...))`; `db.session.execute(db.select(Model).where(...))` |
| Flask ≥ 2.3 | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder`, `JSON_AS_ASCII` | lógica em `create_app()` / `with app.app_context()`, `app.json` provider |
| Werkzeug | `werkzeug.urls.url_quote`, `safe_str_cmp` | `urllib.parse.quote`, `hmac.compare_digest` |
| Node.js | `new Buffer(`, `url.parse(`, `fs.exists(`, `util.isArray(`, `crypto.createCipher(`, `querystring` | `Buffer.from(`, `new URL(`, `fs.existsSync`/`fs.promises.access`, `Array.isArray`, `crypto.createCipheriv(`, `URLSearchParams` |
| Express 4 → 5 | `req.param(`, `res.send(status)`, `res.json(status, obj)`, `res.sendfile(`, `app.del(`, pacote `body-parser` separado | `req.params/req.query/req.body`, `res.sendStatus()`, `res.status(s).json(obj)`, `res.sendFile(`, `app.delete(`, `express.json()` |
| Node (padrão legado) | APIs de driver só com callback quando há alternativa baseada em Promise (ex.: `sqlite3` + callbacks aninhados) | `util.promisify` / wrapper async ou driver com Promises; `async/await` |
| Java | `new Date()` p/ lógica de datas, `Vector`, `Hashtable` | `java.time.*`, `ArrayList`, `HashMap`/`ConcurrentHashMap` |
| PHP | `mysql_*`, `each()`, `create_function` | PDO / mysqli com prepared statements, `foreach`, closures |

**Como verificar:** para cada linha da tabela aplicável à stack, rode o `grep -n` do sinal; confirme a versão instalada/declarada antes de classificar a severidade.
