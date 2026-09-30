# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Toda a configuração vem de variáveis de ambiente (ou de um arquivo `.env`, carregado automaticamente). Copie `.env.example` para `.env` e defina ao menos `SECRET_KEY`; sem ela, uma chave aleatória é gerada a cada boot (os tokens emitidos deixam de valer ao reiniciar). Por padrão o servidor escuta em `127.0.0.1:5000`, com debug desligado e sem CORS para origens externas (`CORS_ORIGINS`).

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o como `Authorization: Bearer <token>` para as operações administrativas:

- `DELETE /users/<id>` exige um usuário `admin`;
- definir `role` diferente de `user` em `POST /users`, ou alterar `role`/`active` em `PUT /users/<id>`, exige um usuário `admin`.

## Estrutura

```
app.py            composition root (create_app) + lançador
config/           settings (env) e constantes de domínio
models/           entidades SQLAlchemy e todo o acesso a dados
controllers/      casos de uso: validação e regras de negócio
routes/           blueprints HTTP finos (camada View)
middlewares/      error handler central e autenticação
services/         tokens assinados e notificações por e-mail
utils/            helpers genéricos (datas, validadores)
```
