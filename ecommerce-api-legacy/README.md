# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
npm install
cp .env.example .env   # preencha PAYMENT_GATEWAY_KEY e ADMIN_API_TOKEN
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória (`DB_FILE`) e já carrega seeds automaticamente no boot.

## Autenticação

- `POST /api/checkout` é público para e-mails novos (cria a conta do aluno). Para um e-mail já cadastrado, `pwd` precisa conferir com a senha da conta, caso contrário a resposta é `401`.
- `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `Authorization: Bearer <ADMIN_API_TOKEN>`.

## Estrutura

```
src/
├── app.js          # composition root
├── config/         # variáveis de ambiente e constantes
├── database/       # conexão (wrapper Promise + transações), schema e seed
├── models/         # acesso a dados (SQL parametrizado)
├── services/       # casos de uso e gateway de pagamento
├── validators/     # validação de entrada
├── controllers/    # adaptação HTTP ↔ serviços
├── routes/         # mapeamento URL → controller
├── middlewares/    # auth, async handler, error handler
└── utils/          # logger e hash de senha
```

Exemplos de requisições estão em `api.http`.
