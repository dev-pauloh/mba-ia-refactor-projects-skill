# Referência — Análise de Projeto (Fase 1)

Heurísticas para descobrir **linguagem, framework, banco de dados, domínio e arquitetura atual** de qualquer codebase de backend. Use sempre **evidência do código** (manifesto, import, linha) e nunca suposição.

---

## 1. Delimitar o escopo (o que conta como "source file")

Inclua arquivos de código-fonte da aplicação. **Exclua** sempre:

| Excluir | Motivo |
|---|---|
| `.git/`, `.claude/`, `.idea/`, `.vscode/` | metadados de ferramentas |
| `node_modules/`, `vendor/`, `.venv/`, `venv/`, `env/`, `__pycache__/`, `target/`, `dist/`, `build/` | dependências e artefatos |
| `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`, `go.sum` | lockfiles |
| `*.db`, `*.sqlite`, `*.log`, binários, imagens | dados |

Comando sugerido (ajuste as extensões à stack detectada):

```bash
find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.mjs' -o -name '*.cjs' \
  -o -name '*.java' -o -name '*.go' -o -name '*.rb' -o -name '*.php' -o -name '*.cs' \) \
  -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/venv/*' \
  -not -path '*/.git/*' -not -path '*/.claude/*' -not -path '*/__pycache__/*' | sort
```

Conte **linhas totais** com `wc -l` sobre a mesma lista. Reporte arquivos vazios (ex.: `__init__.py` de 0-1 linha) na contagem, mas saiba que não têm lógica.

---

## 2. Detectar linguagem e framework

### 2.1 Manifestos (fonte primária, porque trazem versão)

| Manifesto | Linguagem | Onde achar o framework e a versão |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | linha `flask==3.1.1`, `django>=4`, `fastapi` |
| `package.json` | JavaScript / TypeScript (TS se houver `typescript` ou `tsconfig.json`) | `dependencies.express`, `@nestjs/core`, `fastify`, `koa` |
| `pom.xml`, `build.gradle` | Java/Kotlin | `spring-boot-starter-web` |
| `go.mod` | Go | `github.com/gin-gonic/gin`, `echo`, `fiber` |
| `composer.json` | PHP | `laravel/framework`, `symfony/*` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `*.csproj` | C# | `Microsoft.AspNetCore.*` |

A versão reportada é a **declarada no manifesto**. Se houver range (`^4.18.2`), reporte como está e, se existir lockfile, informe também a versão resolvida.

### 2.2 Imports (confirmação, porque o manifesto pode mentir ou estar incompleto)

| Framework | Sinais no código |
|---|---|
| Flask | `from flask import Flask`, `Flask(__name__)`, `Blueprint(`, `@app.route`, `app.add_url_rule` |
| Django | `django.urls`, `models.Model`, `settings.py`, `manage.py` |
| FastAPI | `FastAPI()`, `@app.get`, `APIRouter` |
| Express | `require('express')` / `import express`, `express()`, `app.get(`, `express.Router()` |
| NestJS | `@Controller(`, `@Module(` |
| Spring | `@RestController`, `@SpringBootApplication` |

### 2.3 Dependências relevantes
Liste as dependências **além do framework** que influenciam a arquitetura: ORM, driver de banco, CORS, validação, auth, HTTP client, dotenv. Aponte também as **declaradas e não usadas** (ex.: `marshmallow` no manifesto sem nenhum `import marshmallow`), porque isso vira finding LOW.

---

## 3. Detectar banco de dados e tabelas

| Sinal | Conclusão |
|---|---|
| `import sqlite3`, `sqlite3.connect(`, `require('sqlite3')`, `new sqlite3.Database(` | SQLite com driver cru (SQL manual) |
| `':memory:'` | SQLite **em memória**, cujos dados somem a cada boot |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model` | SQLAlchemy (ORM) |
| `SQLALCHEMY_DATABASE_URI`, `DATABASE_URL` | string de conexão (procure credenciais nela) |
| `sequelize`, `typeorm`, `prisma`, `mongoose`, `knex`, `pg`, `mysql2` | ORM/driver Node |

**Tabelas:** procure `CREATE TABLE <nome>` (SQL cru) e `__tablename__ = '<nome>'` / `class X(db.Model)` (ORM), ou `sequelize.define('<nome>'`, `@Entity`. Liste-as na ordem em que são criadas.

**Seed:** procure `INSERT INTO` em código de inicialização, arquivos `seed.*`, `fixtures`. Anote se o seed roda **automaticamente no boot** ou exige um **comando separado** (ex.: `python seed.py`), porque isso é necessário para a validação da Fase 3.

---

## 4. Entry point, comando de execução e porta

| Stack | Onde procurar |
|---|---|
| Python | `if __name__ == '__main__':` + `app.run(...)`; README ("como rodar") |
| Node | `package.json` → `scripts.start` e `main`; `app.listen(` |
| Geral | `Dockerfile` (`CMD`), `Procfile`, `Makefile` |

Registre o **comando de start**, a **porta** (literal ou config) e **pré-passos** (seed, migrations). A refatoração **deve preservar esse comando**.

---

## 5. Inventário de rotas (base para o baseline da Fase 3)

Extraia **todas** as rotas com método + path + handler + arquivo:linha.

| Framework | Padrões para `grep -n` |
|---|---|
| Flask | `@.*\.route\(`, `add_url_rule\(`, `Blueprint\(` (atenção ao `url_prefix`) |
| Express | `(app|router)\.(get|post|put|patch|delete)\(`, `app.use\('/prefix'` |
| FastAPI | `@(app|router)\.(get|post|put|patch|delete)\(` |

Marque as rotas **destrutivas** (DELETE, reset, queries arbitrárias) para que a Fase 3 as teste por último.

---

## 6. Inferir o domínio

Use os **substantivos** das tabelas, rotas e classes. Exemplos:
- `produtos, pedidos, itens_pedido, usuarios` → **E-commerce**
- `courses, enrollments, payments` + rota `/checkout` → **LMS / plataforma de cursos com checkout**
- `tasks, categories, users` + `/reports` → **Task Manager / produtividade**

Descreva em uma linha: `Domínio (entidades principais)`.

---

## 7. Classificar a arquitetura atual

| Classificação | Critérios objetivos |
|---|---|
| **Monolítica / sem camadas** | ≤ 5 arquivos concentram rotas + SQL + regra; ou uma classe/arquivo registra rotas **e** acessa o banco; sem pastas de camada |
| **Parcialmente em camadas** | existem pastas como `models/`, `routes/`, `services/`, mas **rotas contêm regra de negócio ou queries**, faltam controllers, services não são usados ou config continua hardcoded |
| **Em camadas (MVC)** | rotas só delegam; controllers orquestram; models encapsulam dados; config centralizada; error handler central |

Justifique a classificação com 1-2 evidências (`arquivo:linha`). **Pastas não são prova de arquitetura**: verifique o que cada arquivo realmente faz.

Mapeie cada arquivo para a(s) responsabilidade(s) que ele exerce hoje:

```
app.py          → config + roteamento + endpoints admin + bootstrap
controllers.py  → validação + regra de negócio + notificações (HTTP-aware)
models.py       → SQL + regra de negócio + serialização (4 domínios)
database.py     → conexão global + schema + seed
```

---

## 8. Saída da Fase 1 (formato obrigatório)

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem> <versão se conhecida>
Framework:     <framework> <versão do manifesto>
Dependencies:  <lista separada por vírgula, exceto o framework>
Database:      <engine> (<driver/ORM>) — <arquivo ou :memory:>
Domain:        <domínio> (<entidades>)
Architecture:  <classificação> — <evidência curta>
Entry point:   <arquivo> (start: `<comando>`, port <porta>)
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <t1>, <t2>, ...
Routes:        <N> endpoints (<M> destrutivos)
================================
```

Em seguida, imprima o **mapa de responsabilidades** da seção 7 e o **inventário de rotas** em tabela curta.
