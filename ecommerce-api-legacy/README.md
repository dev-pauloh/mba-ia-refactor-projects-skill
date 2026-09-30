# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Configuração via variáveis de ambiente (veja `.env.example`). As rotas `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN`; sem essa variável elas respondem `401`:

```bash
ADMIN_TOKEN=changeme npm start
```

Exemplos de requisições estão em `api.http`.
