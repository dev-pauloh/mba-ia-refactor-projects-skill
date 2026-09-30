# Referência — Template do Relatório de Auditoria (Fase 2)

O relatório é o artefato que o humano revisa antes de autorizar a refatoração. Ele precisa ser **consistente entre projetos** (mesmo formato), **verificável** (arquivo:linha reais) e **acionável** (cada finding aponta o padrão de correção).

## Regras de preenchimento

1. **Ordem:** todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, ordene por impacto (segurança antes de arquitetura antes de qualidade).
2. **Numeração:** findings numerados sequencialmente (`F01`, `F02`, …) na ordem final; a Fase 3 referencia esses IDs.
3. **Localização (`File:`):** caminho relativo à raiz do projeto + linha(s) reais. Formatos aceitos:
   - `models.py:28` (linha única)
   - `models.py:171-233` (intervalo)
   - `models.py:28, 47-50, 57-61` (várias linhas no mesmo arquivo)
   - Vários arquivos: uma linha `File:` por arquivo.
4. **Description:** o que o código faz **concretamente** (cite o trecho/identificador), não uma definição genérica do anti-pattern.
5. **Impact:** consequência prática (o que um atacante/desenvolvedor/usuário sofre).
6. **Recommendation:** ação específica + ID do playbook (`PB-xx`).
7. **Summary:** as contagens devem bater com a quantidade de findings listados; `Total` = soma.
8. **APIs deprecated:** sempre informe o resultado da verificação na seção própria (mesmo que "nenhuma encontrada").
9. Linhas de código ≈ soma de `wc -l` dos source files da Fase 1 (arredonde para dezenas).
10. Sem emojis; mantenha os separadores `================================` exatamente como abaixo.

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <Linguagem> + <Framework> <versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### F01 [CRITICAL] <Título curto> (AP-xx)
File: <arquivo>:<linhas>
Description: <o que o código faz, com identificadores reais>
Impact: <consequência prática>
Recommendation: <ação concreta> (PB-xx)

### F02 [CRITICAL] ...

### F0n [HIGH] ...

### F0n [MEDIUM] ...

### F0n [LOW] ...

## Deprecated APIs
| API usada | Local | Versão detectada | Substituir por |
|---|---|---|---|
| <api> | <arquivo:linha> | <lib x.y> | <equivalente moderno> |
(ou: "Nenhuma API deprecated encontrada para <stack/versões>.")

## Architecture verdict
Current: <classificação da Fase 1>
Target:  MVC — <1 frase sobre a principal mudança estrutural necessária>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Exemplo preenchido (trecho)

```
### F01 [CRITICAL] SQL Injection em queries de produtos e usuários (AP-02)
File: models.py:28, 47-50, 57-61, 109-111
Description: get_produto_por_id, criar_produto, atualizar_produto e login_usuario montam SQL
concatenando valores do request ("... WHERE email = '" + email + "' AND senha = '" + senha + "'").
Impact: bypass de login com ' OR '1'='1 e leitura/alteração arbitrária do banco.
Recommendation: usar queries parametrizadas com placeholders ? em todas as chamadas execute (PB-02).

### F02 [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7
File: controllers.py:289
Description: SECRET_KEY definida como literal 'minha-chave-super-secreta-123' e devolvida no JSON de /health.
Impact: qualquer leitor do repositório ou cliente de /health obtém a chave de assinatura de sessão.
Recommendation: ler SECRET_KEY de variável de ambiente em config/settings e removê-la do health (PB-01, PB-06).
```
