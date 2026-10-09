# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Organizada em camadas MVC: `routes/` (apresentação HTTP) → `controllers/` (validação e orquestração) → `services/` (regras e acesso ao ORM) → `models/`, com `config/`, `middlewares/` (autenticação e erros) e `app.py` como composition root.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: defina SECRET_KEY e demais variáveis
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (`HOST`/`PORT` configuráveis). O `seed.py` limpa e popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**. Se `SECRET_KEY` não estiver definida, uma chave aleatória é gerada a cada boot (tokens anteriores deixam de valer).

## Autenticação

Faça login e envie o token no header `Authorization: Bearer <token>`:

```bash
curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email": "joao@email.com", "password": "joao1234"}'
```

| Acesso | Rotas |
|---|---|
| Público | `GET /`, `GET /health`, `POST /login` |
| Usuário autenticado | `/tasks` (todas), `GET /categories` |
| Próprio usuário ou admin/manager | `GET /users/<id>`, `GET /users/<id>/tasks`, `GET /reports/user/<id>` |
| Próprio usuário ou admin (só admin altera `role`/`active`) | `PUT /users/<id>` |
| admin ou manager | `GET /users`, `GET /reports/summary`, `POST/PUT/DELETE /categories` |
| admin | `POST /users`, `DELETE /users/<id>` |

Usuários do seed: `joao@email.com` / `joao1234` (admin), `maria@email.com` / `maria1234` (user), `pedro@email.com` / `pedro1234` (manager). Senhas exigem no mínimo 8 caracteres.
