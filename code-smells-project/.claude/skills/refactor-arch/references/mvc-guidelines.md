# Referência — Guidelines de Arquitetura MVC (Fase 3)

Define **a arquitetura-alvo**: quais camadas existem, o que cada uma pode e não pode fazer, e como organizar os arquivos em cada stack. Em uma API REST, a "View" é a **camada de apresentação HTTP** (rotas + serialização da resposta), não um template HTML.

---

## 1. Camadas e responsabilidades

| Camada | Responsabilidade | PODE | NÃO PODE |
|---|---|---|---|
| **Config** (`config/`) | Centralizar configuração e constantes | ler variáveis de ambiente, definir defaults **não secretos**, constantes de domínio (status válidos, limites) | conter segredos literais; importar outras camadas |
| **Model** (`models/`) | Representar entidades e **encapsular acesso a dados** | SQL parametrizado / ORM, mapeamento row→objeto/dict, regras intrínsecas da entidade (`is_overdue`, `check_password`) | importar `request`/`req`/`res`/`jsonify`; conhecer HTTP; enviar e-mail; ler config diretamente de literais |
| **Controller** (`controllers/`) | **Orquestrar o caso de uso**: validar entrada, aplicar regras de negócio, coordenar models e services, decidir o resultado | chamar models/services, lançar erros de domínio (`NotFoundError`, `ValidationError`), montar dados de retorno | acessar o banco com SQL direto; conhecer detalhes de framework HTTP além do necessário; formatar respostas HTTP (status/JSON) |
| **View / Routes** (`views/` ou `routes/`) | **Apresentação HTTP**: mapear URL+método → controller, extrair parâmetros do request, serializar a resposta com status | ler `request`/`req`, chamar **um** método de controller, `jsonify`/`res.json`, escolher status de sucesso | conter regra de negócio, loops de agregação, queries, try/except genérico |
| **Services** (`services/`, opcional) | Integrações externas e efeitos colaterais reutilizáveis | e-mail, gateway de pagamento, notificações, cache | conter regra de domínio central; ser instanciado dentro de models |
| **Middlewares** (`middlewares/`) | Preocupações transversais | error handler central, autenticação/autorização, logging de requisição | regra de negócio |
| **Database** (`database/` ou `models/db`) | Conexão, schema e seed | fábrica de conexão/sessão, criação de tabelas, seed idempotente | ser um global mutável compartilhado sem controle |
| **Composition root** (`app.py`, `src/app.js`) | Montar a aplicação | carregar config, iniciar banco, registrar rotas/blueprints, middlewares e error handlers, iniciar servidor | conter rotas com lógica, SQL ou regra |

## 2. Regra de dependência

```
View/Routes ──► Controllers ──► Models
      │               └──────► Services
      └──► Middlewares
Config ◄── (todas as camadas podem ler config)
Composition root ──► monta tudo (única camada que conhece todas)
```

- Dependências **só apontam para dentro/baixo**; nunca Model → Controller, nunca Controller → View.
- Nenhum import circular.
- Infraestrutura (conexão, SMTP, gateway) é **injetada** ou obtida por fábrica (`get_db()` por requisição, `app.extensions`, construtor), nunca criada em módulo global mutável.

## 3. Estrutura-alvo por stack

### 3.1 Python / Flask — projeto monolítico (sem camadas)
Crie um pacote `src/` e mantenha o **entry point original** como lançador fino, para preservar o comando de start.

```
<projeto>/
├── app.py                      # lançador: from src.app import create_app; create_app().run(...)
├── requirements.txt
├── .env.example
└── src/
    ├── __init__.py
    ├── app.py                  # composition root: create_app()
    ├── config/
    │   ├── __init__.py
    │   └── settings.py         # Settings lidas de os.environ + constantes
    ├── database/
    │   ├── __init__.py
    │   └── connection.py       # get_db() por app context, init_db(), seed
    ├── models/
    │   ├── __init__.py
    │   └── <entidade>_model.py # uma por entidade/agregado
    ├── controllers/
    │   ├── __init__.py
    │   └── <entidade>_controller.py
    ├── services/               # se houver efeitos colaterais (notificação, pagamento)
    ├── views/
    │   ├── __init__.py
    │   └── <entidade>_routes.py  # Blueprints finos
    └── middlewares/
        ├── __init__.py
        ├── error_handler.py    # AppError + @app.errorhandler
        └── auth.py             # decorator p/ rotas administrativas
```

### 3.2 Python / Flask — projeto já parcialmente em camadas
**Não mova tudo para `src/`**; complete e corrija a estrutura existente, minimizando churn:
- mantenha `models/`, `routes/` (que passa a ser a camada **View**), `services/`, `utils/`;
- **adicione** `controllers/` e mova para lá a lógica que hoje está nas rotas;
- **adicione** `config/settings.py` e `middlewares/error_handler.py`;
- transforme `app.py` em composition root com `create_app()`;
- use (ou remova) utilitários/constantes existentes que estavam mortos — não mantenha duplicatas.

### 3.3 Node.js / Express
O entry point costuma ser `src/app.js` (ver `package.json`). Mantenha-o como composition root.

```
<projeto>/
├── package.json                # scripts.start inalterado
├── .env.example
└── src/
    ├── app.js                  # composition root: cria app, db, rotas, error handler, listen
    ├── config/
    │   └── index.js            # config lida de process.env + constantes
    ├── database/
    │   └── connection.js       # abre DB, wrapper async (promisify), schema + seed
    ├── models/
    │   └── <entidade>Model.js  # classes/funções com SQL parametrizado, async
    ├── controllers/
    │   └── <entidade>Controller.js
    ├── services/
    │   └── <servico>Service.js # ex.: paymentService (gateway), cacheService
    ├── routes/                 # camada View (express.Router)
    │   └── <entidade>Routes.js
    └── middlewares/
        ├── errorHandler.js     # (err, req, res, next)
        ├── asyncHandler.js     # captura rejeições de handlers async
        └── auth.js
```

### 3.4 Outras stacks (mesmo princípio)
- **Django:** `models.py` (Model), `views.py` (Controller no vocabulário MVC), `urls.py` + serializers (View/apresentação); settings via env.
- **FastAPI:** `routers/` (View), `controllers/` ou `services/`, `models/` + `schemas/`, `core/config.py`.
- **Spring:** `@RestController` (View), `@Service` (Controller/caso de uso), `@Repository`/`@Entity` (Model), `application.yml` com placeholders `${ENV}`.

## 4. Convenções

- **Um arquivo por entidade/agregado** em models, controllers e views (`produto_model.py`, `produto_controller.py`, `produto_routes.py`).
- Nomes em inglês ou português seguem **a língua predominante do projeto**; não misture no mesmo nível.
- Rotas finas: idealmente ≤ 10 linhas por handler.
- Controllers retornam **dados** (dict/objeto) ou lançam erro de domínio; a View decide o status HTTP de sucesso; o error handler decide o status de erro.
- Erros de domínio mapeados centralmente: `ValidationError → 400`, `UnauthorizedError → 401`, `ForbiddenError → 403`, `NotFoundError → 404`, `ConflictError → 409`, inesperado → `500` com mensagem genérica (detalhe só no log).
- Logging via `logging` (Python) / logger central (Node), nunca `print`/`console.log` soltos.

## 5. Configuração e segredos

- Todo segredo vem de variável de ambiente. Se ausente em desenvolvimento, **gere um valor aleatório em runtime** (`secrets.token_hex(32)` / `crypto.randomBytes(32)`) e emita warning — nunca um literal no código.
- Valores não secretos (porta, caminho do banco, flags) podem ter default seguro (`DEBUG` default **false**).
- Carregue `.env` se o projeto já tiver `python-dotenv`/`dotenv`; caso contrário, `os.environ`/`process.env` bastam.
- Crie `.env.example` listando todas as variáveis com valores fictícios.

## 6. Preservação do contrato da API

O objetivo é que **os clientes existentes continuem funcionando**:
- mesmos paths, métodos HTTP, formato do corpo aceito (inclusive nomes de campos, mesmo que ruins — renomeie só internamente), códigos de status de sucesso e chaves de topo do JSON de resposta;
- mesmo envelope de erro que o projeto já usa (ex.: `{"erro": ...}` vs `{"error": ...}`).

**Mudanças de contrato permitidas (e obrigatórias quando o finding existir)** — sempre listadas em "Intentional contract changes":
1. Remover campos sensíveis das respostas (`senha`, `password`, hash, `secret_key`, config interna).
2. **Toda rota citada em qualquer finding CRITICAL — e toda rota citada em finding de qualquer severidade cuja Recommendation seja autenticação/autorização ou cujo Impact descreva acesso/exposição sem identidade (ex.: "qualquer um lista usuários, pedidos e faturamento") — recebe autenticação, sem exceção de categoria.** Vale para qualquer anti-pattern (AP-01 a AP-06) e para qualquer tipo de rota: administrativa, destrutiva, CRUD comum ou de leitura (`DELETE /tasks/<id>`, `DELETE /categories/<id>`, `GET /usuarios`, `GET /health` etc.). "Citada" = a rota aparece no finding como `MÉTODO /path` (ver SKILL.md, Fase 2). A autenticação **soma-se** à correção específica do finding (ex.: parametrizar a query continua obrigatório).
   - **Única exceção — a rota que emite a credencial** (login / obtenção de token): ela não pode exigir a credencial que ela própria emite, senão ninguém consegue se autenticar. Essa rota recebe a correção do seu finding e aparece explicitamente como exceção em "Intentional contract changes". Nenhuma outra rota pode usar essa exceção.
   - **Mecanismo:** reutilize o que o projeto já tem ou passou a ter na refatoração. Se existe login, use token assinado (`Authorization: Bearer <token>`, PB-13). Se não existe, use token de API configurado no ambiente (header `X-API-Token` comparado com `API_TOKEN`) e, para rotas administrativas, `X-Admin-Token` comparado com `ADMIN_TOKEN` — sempre em tempo constante.
   - **Autorização:** exija papel de admin quando o finding fala em privilégio, gestão de usuários, dados de outros usuários ou operações administrativas; nos demais casos basta estar autenticado.
   - Sem credencial → `401`; credencial sem permissão → `403`; credencial válida → comportamento original.
   - Também recebem autenticação de admin os paths administrativos/destrutivos globais (`admin`, `reset`, `query`, relatórios financeiros), mesmo que nenhum finding CRITICAL os cite.
3. Endpoints que executam **código ou SQL arbitrário** enviados pelo cliente: além de exigir admin, ficam **desabilitados por padrão** por flag de config (ex.: `ENABLE_ADMIN_SQL=false` → `403`).
4. Entradas inválidas que antes geravam `500` passam a gerar `400`.
5. Endpoints **que não são citados em nenhum finding coberto pela regra 2** (nem são administrativos/destrutivos globais) continuam sem autenticação, para não quebrar clientes; registre-os como recomendação residual no resumo. Esta regra **nunca** se sobrepõe à regra 2: nada que apareça no Impact de um finding pode virar recomendação residual.

> **Rastreabilidade:** a seção "Findings addressed" do resumo final lista, para cada finding coberto pela regra 2 (CRITICAL ou de autenticação/exposição em qualquer severidade), **cada rota citada** e o mecanismo de autenticação aplicado (ou "exceção: emite credencial"). Rota citada e não protegida = finding não resolvido = validação reprovada.

## 7. Checklist de conformidade (use na validação)

- [ ] Estrutura de diretórios segue §3 da stack
- [ ] Nenhum segredo literal; config em módulo próprio; `.env.example` criado
- [ ] Models encapsulam todo acesso a dados (nenhum SQL/ORM em views/controllers)
- [ ] Views/Routes só delegam (sem regra de negócio)
- [ ] Controllers concentram o fluxo do caso de uso
- [ ] Error handling centralizado (sem `try/except` genérico repetido nas rotas)
- [ ] Entry point claro (composition root) e comando de start preservado
- [ ] App inicia sem erros; endpoints do baseline respondem
