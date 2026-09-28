# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas como hash).

## Configuração

Toda a configuração vem de variáveis de ambiente; veja `.env.example`. As principais:

| Variável | Uso |
|---|---|
| `SECRET_KEY` | chave do Flask (se ausente, é gerada aleatoriamente a cada boot) |
| `ADMIN_TOKEN` | exigido no header `X-Admin-Token` em `/admin/*` e `/relatorios/vendas` |
| `ENABLE_ADMIN_SQL` | habilita `POST /admin/query` (padrão `false`) |
| `FLASK_DEBUG`, `HOST`, `PORT` | servidor (padrões: `false`, `127.0.0.1`, `5000`) |
| `CORS_ORIGINS` | origens permitidas, separadas por vírgula (vazio = CORS desabilitado) |

## Estrutura

```
app.py              lançador (python app.py)
src/app.py          composition root (create_app)
src/config/         settings (env) e constantes de domínio
src/database/       conexão por requisição, schema e seed
src/models/         acesso a dados por entidade (SQL parametrizado)
src/controllers/    casos de uso, validação e regras de negócio
src/services/       notificações
src/views/          Blueprints (rotas HTTP)
src/middlewares/    error handler central e autenticação admin
```
