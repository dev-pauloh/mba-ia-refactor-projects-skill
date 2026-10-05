# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, organizada em MVC: `routes/` (View HTTP), `controllers/` (casos de uso), `models/` (dados), `services/` (token e notificações), `middlewares/` (auth e erros) e `config/` (settings via ambiente e constantes).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # ajuste SECRET_KEY e demais variáveis
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (`HOST`/`PORT` configuráveis). O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Autenticação

`POST /login` devolve um `token` assinado (expira em `TOKEN_MAX_AGE` segundos). Envie-o como `Authorization: Bearer <token>` nas rotas protegidas:

| Acesso | Rotas |
|---|---|
| Público | `GET /`, `GET /health`, `POST /login`, `GET/POST /tasks`, `GET/PUT /tasks/<id>`, `GET /tasks/search`, `GET /tasks/stats`, `GET /users/<id>/tasks` |
| Autenticado | `DELETE /tasks/<id>`, `GET/POST /categories`, `PUT/DELETE /categories/<id>` |
| Próprio usuário ou admin | `GET /users/<id>`, `PUT /users/<id>` (só admin altera `role`/`active`), `GET /reports/user/<id>` |
| Admin | `GET /users`, `POST /users`, `DELETE /users/<id>`, `GET /reports/summary` |

Sem `SECRET_KEY` definida, uma chave aleatória é gerada a cada boot (tokens anteriores deixam de valer).
