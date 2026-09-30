# Referência — Playbook de Refatoração (Fase 3)

Padrões concretos de transformação. Cada padrão (`PB-xx`) corrige um ou mais anti-patterns (`AP-xx`) do catálogo e traz exemplos **antes → depois** em Python e/ou JavaScript. Adapte nomes e estilo ao projeto; o princípio é o que importa.

| ID | Padrão | Corrige |
|---|---|---|
| PB-01 | Extrair configuração e segredos para módulo de config + env | AP-01, AP-10 |
| PB-02 | Parametrizar queries SQL | AP-02 |
| PB-03 | Decompor God Class/File em camadas MVC | AP-03 |
| PB-04 | Mover regra de negócio da rota para o controller | AP-07 |
| PB-05 | Substituir estado global por fábrica/injeção de dependência | AP-08, AP-09 |
| PB-06 | Hash seguro de senha e remoção de dados sensíveis | AP-04, AP-06 |
| PB-07 | Eliminar N+1 com JOIN / eager loading / GROUP BY | AP-13 |
| PB-08 | Callbacks aninhados → async/await | AP-11, AP-22 (padrão legado) |
| PB-09 | Error handling centralizado | AP-17 |
| PB-10 | Transações em operações multi-etapa | AP-14 |
| PB-11 | Substituir APIs deprecated | AP-22 |
| PB-12 | Constantes nomeadas e validação única | AP-15, AP-16, AP-18, AP-19 |
| PB-13 | Proteger endpoints administrativos / token assinado | AP-05, AP-12 |
| PB-14 | Logging estruturado e remoção de código morto | AP-20, AP-21 |

---

## PB-01 — Extrair configuração e segredos

**Python — antes**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
...
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Python — depois** (`src/config/settings.py`)
```python
import os
import secrets
import logging

logger = logging.getLogger(__name__)

def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes")

def _secret(name):
    value = os.environ.get(name)
    if not value:
        logger.warning("%s não definida; usando valor aleatório (apenas desenvolvimento)", name)
        value = secrets.token_hex(32)
    return value

class Settings:
    SECRET_KEY = _secret("SECRET_KEY")
    DEBUG = _env_bool("FLASK_DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
```
```python
# src/app.py (composition root)
def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)
    ...
    return app

# app.py (lançador na raiz — comando de start preservado)
from src.app import create_app
from src.config.settings import Settings

app = create_app()
if __name__ == "__main__":
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
```

**Node — antes**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123...", port: 3000 };
```
**Node — depois** (`src/config/index.js`)
```js
const crypto = require('crypto');

function secret(name) {
  if (process.env[name]) return process.env[name];
  console.warn(`[config] ${name} não definida; usando valor aleatório (apenas desenvolvimento)`);
  return crypto.randomBytes(32).toString('hex');
}

module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  dbFile: process.env.DB_FILE || ':memory:',
  paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
  adminToken: process.env.ADMIN_TOKEN || '',
});
```
Crie `.env.example` com `SECRET_KEY=`, `ADMIN_TOKEN=`, `PORT=5000` etc.

---

## PB-02 — Parametrizar queries SQL

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("UPDATE pedidos SET status = '" + novo_status + "' WHERE id = " + str(pedido_id))
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
```

**Filtros dinâmicos — antes**
```python
query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
if categoria:
    query += " AND categoria = '" + categoria + "'"
```
**Depois** (só a *estrutura* é montada dinamicamente; valores sempre como parâmetros)
```python
clauses, params = [], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    clauses.append("categoria = ?")
    params.append(categoria)
where = " AND ".join(clauses) or "1=1"
cursor.execute(f"SELECT * FROM produtos WHERE {where}", params)
```
**Node**
```js
// antes: db.get(`SELECT * FROM users WHERE email = '${email}'`)
const user = await db.get('SELECT id FROM users WHERE email = ?', [email]);
```

---

## PB-03 — Decompor God Class / God File em camadas

**Antes** (uma classe faz banco, rotas e regra)
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE ... INSERT ... */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* valida, consulta, cobra, grava, responde */ });
    app.get('/api/admin/financial-report', (req, res) => { /* agrega */ });
  }
}
```
**Depois** (cada responsabilidade em sua camada; o composition root monta)
```js
// src/models/courseModel.js — só dados
class CourseModel {
  constructor(db) { this.db = db; }
  findActiveById(id) { return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]); }
}

// src/controllers/checkoutController.js — fluxo do caso de uso
class CheckoutController {
  constructor({ courseModel, userModel, enrollmentModel, paymentService }) { Object.assign(this, { courseModel, userModel, enrollmentModel, paymentService }); }
  async checkout({ name, email, password, courseId, cardNumber }) {
    const course = await this.courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');
    /* ... */
    return { enrollmentId };
  }
}

// src/routes/checkoutRoutes.js — View HTTP fina
module.exports = (controller) => {
  const router = express.Router();
  router.post('/api/checkout', asyncHandler(async (req, res) => {
    const { usr, eml, pwd, c_id, card } = req.body;          // contrato público preservado
    const result = await controller.checkout({ name: usr, email: eml, password: pwd, courseId: c_id, cardNumber: card });
    res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
  }));
  return router;
};

// src/app.js — composition root
const db = await createDatabase(config.dbFile);
const checkoutController = new CheckoutController({ courseModel: new CourseModel(db), /* ... */ });
app.use(checkoutRoutes(checkoutController));
app.use(errorHandler);
```

**Python (monolito de funções)** — divida `models.py` por entidade (`produto_model.py`, `usuario_model.py`, `pedido_model.py`), mova validação/regra de `controllers.py` para `controllers/<entidade>_controller.py` e o registro de rotas de `app.py` para `views/<entidade>_routes.py` com Blueprints:
```python
# src/views/produto_routes.py
bp = Blueprint("produtos", __name__)

@bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    produto = produto_controller.buscar(produto_id)      # lança NotFoundError se não existir
    return jsonify({"dados": produto, "sucesso": True}), 200
```

---

## PB-04 — Mover regra de negócio da rota para o controller

**Antes** (rota calcula tudo)
```python
@report_bp.route('/reports/user/<int:user_id>')
def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    tasks = Task.query.filter_by(user_id=user_id).all()
    done = 0
    for t in tasks:
        if t.status == 'done':
            done = done + 1
    ...
    return jsonify(report), 200
```
**Depois**
```python
# controllers/report_controller.py
def user_report(user_id):
    user = user_model.get_or_404(user_id)          # NotFoundError → 404 via error handler
    tasks = task_model.list_by_user(user_id)
    stats = Counter(t.status for t in tasks)
    total = len(tasks)
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": stats["done"],
            "overdue": sum(1 for t in tasks if t.is_overdue()),
            "completion_rate": percentage(stats["done"], total),
            ...
        },
    }

# routes/report_routes.py (View)
@report_bp.get('/reports/user/<int:user_id>')
def user_report(user_id):
    return jsonify(report_controller.user_report(user_id)), 200
```
Efeitos colaterais (e-mail/SMS/push, auditoria) saem do handler para um **service** chamado pelo controller:
```python
# antes (controller)
print("ENVIANDO EMAIL: Pedido " + str(pedido_id) + " criado")
# depois
notification_service.pedido_criado(pedido_id, usuario_id)   # service com logging/integração real
```

---

## PB-05 — Estado global → fábrica / injeção de dependência

**Python — antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```
**Python — depois** (uma conexão por requisição, fechada no teardown)
```python
from flask import g, current_app
import sqlite3

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        create_schema(get_db())
        seed_if_empty(get_db())
```

**Node — antes**
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
module.exports = { globalCache, logAndCache };
```
**Node — depois** (estado encapsulado em serviço, instanciado no composition root e injetado)
```js
class CacheService {
  #store = new Map();
  constructor({ maxEntries = 1000 } = {}) { this.maxEntries = maxEntries; }
  set(key, value) {
    if (this.#store.size >= this.maxEntries) this.#store.delete(this.#store.keys().next().value);
    this.#store.set(key, value);
  }
  get(key) { return this.#store.get(key); }
}
// app.js: const cache = new CacheService(); new CheckoutController({ ..., cache });
```
Serviços com integrações (SMTP, gateway) recebem config pelo construtor em vez de ler literais.

---

## PB-06 — Hash seguro de senha e remoção de dados sensíveis

**Python — antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
...
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```
**Python — depois** (`werkzeug` já vem com o Flask — sem dependência nova)
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)

def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}   # sem password
```
Login com SQL cru: **não compare senha no WHERE**; busque por email e verifique o hash:
```python
row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
if row is None or not check_password_hash(row["senha"], senha):
    raise UnauthorizedError("Email ou senha inválidos")
```
**Seed:** senhas do seed também passam por `generate_password_hash`. Apague bancos locais de dev gerados antes da mudança (ex.: `loja.db`, `tasks.db`, ignorados pelo git) e rode o seed de novo — senão o login com dados antigos (texto puro/MD5) falha.

**Node — depois** (`crypto.scrypt` nativo — sem dependência nativa como bcrypt)
```js
const crypto = require('crypto');

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, hash] = stored.split(':');
  const candidate = crypto.scryptSync(password, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```
**Logs e health:** nunca logar cartão/senha/chave. Se precisar referenciar cartão, use só os 4 últimos dígitos:
```js
// antes: console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
logger.info(`Processando pagamento cartão final ${cardNumber.slice(-4)}`);
```
Remova `secret_key`, `debug`, `db_path` e afins do JSON do `/health`.

---

## PB-07 — Eliminar N+1

**SQL cru — antes** (1 + P + P·I queries)
```python
for row in cursor.execute("SELECT * FROM pedidos").fetchall():
    itens = db.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"])).fetchall()
    for item in itens:
        prod = db.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"])).fetchone()
```
**Depois** (2 queries, agrupamento em memória)
```python
pedidos = db.execute("SELECT * FROM pedidos").fetchall()
itens = db.execute("""
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(p.nome, 'Desconhecido') AS produto_nome
    FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
""").fetchall()
itens_por_pedido = defaultdict(list)
for item in itens:
    itens_por_pedido[item["pedido_id"]].append(dict(item))
result = [{**dict(p), "itens": itens_por_pedido[p["id"]]} for p in pedidos]
```
Filtrando pedidos (ex.: por usuário), use `WHERE i.pedido_id IN (SELECT id FROM pedidos WHERE usuario_id = ?)`.

**SQLAlchemy — antes**
```python
for t in Task.query.all():
    user = User.query.get(t.user_id)
    cat = Category.query.get(t.category_id)
```
**Depois**
```python
from sqlalchemy.orm import joinedload
tasks = db.session.execute(
    db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
).scalars().all()
# t.user.name e t.category.name já carregados
```
**Contagens repetidas → GROUP BY**
```python
# antes: pending = Task.query.filter_by(status='pending').count(); done = ...; (4-5 queries)
rows = db.session.execute(db.select(Task.status, db.func.count()).group_by(Task.status)).all()
by_status = {status: 0 for status in VALID_STATUSES} | dict(rows)
```
**Node — relatório com JOIN único**
```js
const rows = await db.all(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u       ON u.id = e.user_id
  LEFT JOIN payments p    ON p.enrollment_id = e.id
  ORDER BY c.id, e.id`);
// agrupe por course_id em memória preservando o formato de resposta original
```

---

## PB-08 — Callbacks aninhados → async/await

**Antes**
```js
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
  if (err || !course) return res.status(404).send("Curso não encontrado");
  this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
    this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
      self.db.run("INSERT INTO payments ...", [this.lastID, ...], function (err) { /* ... */ });
    });
  });
});
```
**Depois** — wrapper Promise sobre o driver (`src/database/connection.js`)
```js
const sqlite3 = require('sqlite3');

class Database {
  constructor(filename) { this.conn = new sqlite3.Database(filename); }
  run(sql, params = []) {
    return new Promise((resolve, reject) =>
      this.conn.run(sql, params, function (err) {
        if (err) reject(err); else resolve({ lastID: this.lastID, changes: this.changes });
      }));
  }
  get(sql, params = []) {
    return new Promise((resolve, reject) => this.conn.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
  }
  all(sql, params = []) {
    return new Promise((resolve, reject) => this.conn.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));
  }
}
```
Controller linear:
```js
async checkout({ email, courseId, cardNumber, ... }) {
  const course = await this.courseModel.findActiveById(courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');
  const userId = (await this.userModel.findByEmail(email))?.id ?? (await this.userModel.create({ ... }));
  const status = this.paymentService.charge(cardNumber, course.price);
  if (status !== PaymentStatus.PAID) throw new PaymentDeclinedError('Pagamento recusado');
  const enrollmentId = await this.db.transaction(async () => { /* PB-10 */ });
  return { enrollmentId };
}
```

---

## PB-09 — Error handling centralizado

**Antes** (repetido em cada handler)
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500
```
**Depois — Flask** (`src/middlewares/error_handler.py`)
```python
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class AppError(Exception):
    status_code = 500
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

class ValidationError(AppError):   status_code = 400
class UnauthorizedError(AppError): status_code = 401
class ForbiddenError(AppError):    status_code = 403
class NotFoundError(AppError):     status_code = 404
class ConflictError(AppError):     status_code = 409

def register_error_handlers(app, error_key="erro"):
    # error_key: use o envelope que o projeto já usa ("erro" ou "error")
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({error_key: err.message, "sucesso": False}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({error_key: err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({error_key: "Erro interno do servidor"}), 500
```
Handlers ficam sem `try/except`; controllers lançam `NotFoundError(...)` etc. Inclua `"sucesso": False` apenas se o projeto original já usa esse campo.

**Depois — Express**
```js
// src/middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// src/middlewares/errorHandler.js
const { AppError } = require('../errors');
module.exports = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);  // mantém formato original (texto)
  console.error('[error]', err);
  res.status(500).send('Erro interno');
};
// app.js: registre por último → app.use(errorHandler);
```
Python: troque `except:` por exceções específicas (`except ValueError:`), nunca vazio.

---

## PB-10 — Transações em operações multi-etapa

**sqlite3 (Python) — antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
db.commit()
```
**Depois** (`with conn:` faz COMMIT no sucesso e ROLLBACK na exceção)
```python
with db:
    cur = db.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)", (usuario_id, "pendente", total))
    pedido_id = cur.lastrowid
    for item in itens:
        db.execute("INSERT INTO itens_pedido (...) VALUES (?, ?, ?, ?)", (...))
        updated = db.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (item["quantidade"], item["produto_id"], item["quantidade"]),
        ).rowcount
        if updated == 0:
            raise ValidationError(f"Estoque insuficiente para o produto {item['produto_id']}")
```
**SQLAlchemy:** agrupe as alterações e faça um único `db.session.commit()`; em erro, `db.session.rollback()` (o error handler pode fazer isso). Para exclusões com filhos, use `cascade="all, delete-orphan"` no relationship ou apague os filhos explicitamente na mesma transação.

**Node**
```js
async transaction(fn) {             // método do wrapper Database (PB-08)
  await this.run('BEGIN');
  try { const result = await fn(); await this.run('COMMIT'); return result; }
  catch (err) { await this.run('ROLLBACK'); throw err; }
}
// DELETE de usuário: apague payments → enrollments → user dentro da mesma transação.
```
> Com uma única conexão SQLite em Node, serialize transações concorrentes (fila/mutex simples) se o app for sujeito a requisições paralelas.

---

## PB-11 — Substituir APIs deprecated

**SQLAlchemy 2.x**
```python
# antes
task = Task.query.get(task_id)
# depois
task = db.session.get(Task, task_id)
if task is None:
    raise NotFoundError("Task não encontrada")
```
**Python 3.12 — `datetime.utcnow()`**
```python
# antes
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if self.due_date < datetime.utcnow(): ...
# depois — helper único (utils/time.py)
from datetime import datetime, timezone

def utcnow():
    """UTC atual como datetime *naive*, compatível com colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow)
```
> Atenção: comparar um datetime *aware* (`datetime.now(timezone.utc)`) com valores *naive* lidos do SQLite gera `TypeError`. Use o helper acima (ou colunas `DateTime(timezone=True)` de forma consistente).

**Node / Express**
```js
// antes                              // depois
new Buffer(pwd)                        Buffer.from(pwd)
url.parse(req.url)                     new URL(req.url, `http://${req.headers.host}`)
res.send(404)                          res.sendStatus(404)
res.json(201, body)                    res.status(201).json(body)
app.use(bodyParser.json())             app.use(express.json())
```

---

## PB-12 — Constantes nomeadas e validação única

**Magic numbers — antes**
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
elif faturamento > 1000:
    desconto = faturamento * 0.02
```
**Depois**
```python
# config/constants.py
DISCOUNT_TIERS = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))   # (faturamento mínimo exclusivo, taxa)

# controller
def calcular_desconto(faturamento):
    for minimo, taxa in DISCOUNT_TIERS:
        if faturamento > minimo:
            return faturamento * taxa
    return 0
```
**Validação duplicada — antes:** as mesmas checagens copiadas em `criar_produto` e `atualizar_produto` (com divergências).
**Depois:** um validador por entidade, usado pelos dois fluxos:
```python
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")

def validar_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            raise ValidationError(f"{campo.capitalize()} é obrigatório")
    if not isinstance(dados["preco"], (int, float)) or dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    ...
    return {"nome": dados["nome"].strip(), ...}
```
Se o projeto já tem utilitários/constantes (ex.: `VALID_STATUSES`, `process_task_data`) **não usados**, reutilize-os em vez de criar novos — e remova as cópias inline.
**Validação de tipo:** converta e valide antes de comparar (`int(x)` dentro de `try/except (TypeError, ValueError)` → `ValidationError`), para que entrada inválida gere 400 e não 500.
**Nomes:** renomeie variáveis internas (`u, e, p, cid, cc` → `name, email, password, courseId, cardNumber`) mantendo os nomes de campos do contrato público na borda (View).

---

## PB-13 — Proteger endpoints administrativos / token assinado

**Flask — decorator** (`src/middlewares/auth.py`)
```python
import hmac
from functools import wraps
from flask import request, current_app
from .error_handler import UnauthorizedError

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided, expected):
            raise UnauthorizedError("Acesso administrativo requer X-Admin-Token válido")
        return view(*args, **kwargs)
    return wrapper

@bp.post("/admin/reset-db")
@require_admin
def reset_db(): ...
```
Endpoints de SQL/código arbitrário: além de `@require_admin`, verifique `current_app.config["ENABLE_ADMIN_SQL"]` (default `False` → `ForbiddenError`).

**Express — middleware**
```js
const crypto = require('crypto');
module.exports = (config) => (req, res, next) => {
  const provided = Buffer.from(req.get('X-Admin-Token') || '');
  const expected = Buffer.from(config.adminToken);
  if (!expected.length || provided.length !== expected.length || !crypto.timingSafeEqual(provided, expected)) {
    return res.status(401).send('Não autorizado');
  }
  next();
};
// router.get('/api/admin/financial-report', requireAdmin, asyncHandler(...))
```
**Token falso → token assinado** (Flask já inclui `itsdangerous`)
```python
# antes: 'token': 'fake-jwt-token-' + str(user.id)
from itsdangerous import URLSafeTimedSerializer

def issue_token(user_id):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth").dumps({"uid": user_id})

def verify_token(token, max_age=3600):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth").loads(token, max_age=max_age)
```
A chave `token` continua na resposta do login (contrato preservado), agora com valor não forjável.

---

## PB-14 — Logging estruturado e remoção de código morto

**Python — antes**
```python
print("Produto criado com ID: " + str(id))
print("ERRO: " + str(e))
```
**Depois**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Produto criado id=%s", produto_id)
logger.exception("Falha ao criar produto")     # dentro de except, inclui stack trace
```
Configure uma vez no composition root: `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")`.

**Node:** centralize em `src/utils/logger.js` (`info`, `warn`, `error` com prefixo/timestamp) em vez de `console.log` espalhado.

**Código morto — checklist**
- remover imports sem uso (`import os, sys, json` não referenciados);
- remover exports/variáveis nunca lidos (`totalRevenue`);
- remover arquivos antigos **depois** de migrar todo o seu conteúdo (ex.: `controllers.py`, `models.py`, `AppManager.js`, `utils.js`) — confirme com `grep -rn "<nome do módulo>"` que ninguém mais os importa;
- dependências declaradas e não usadas: remova do manifesto **ou** passe a usá-las se resolverem um finding (ex.: `python-dotenv` para carregar `.env`).
