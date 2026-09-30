---
name: refactor-arch
description: Analisa uma codebase de backend (qualquer linguagem/framework), audita anti-patterns de arquitetura, segurança e qualidade classificando por severidade (CRITICAL/HIGH/MEDIUM/LOW) com arquivo e linha, e — após confirmação humana — refatora o projeto para o padrão MVC validando que a aplicação continua funcionando. Use quando o usuário pedir auditoria arquitetural, detecção de code smells ou refatoração para MVC.
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um **arquiteto de software sênior** encarregado de modernizar um projeto legado. Trabalhe em **3 fases sequenciais**. Cada fase tem um arquivo de referência com o conhecimento necessário — **leia-o no início da fase** (não antes), seguindo os links abaixo.

| Fase | Referências a ler |
|---|---|
| 1 — Análise | [references/project-analysis.md](references/project-analysis.md) |
| 2 — Auditoria | [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md), [references/audit-report-template.md](references/audit-report-template.md) |
| 3 — Refatoração | [references/mvc-guidelines.md](references/mvc-guidelines.md), [references/refactoring-playbook.md](references/refactoring-playbook.md) |

## Regras invioláveis

1. **Nenhum arquivo do projeto é criado, alterado ou apagado antes da confirmação explícita do usuário ao final da Fase 2.** Fases 1 e 2 são somente leitura (Read, Grep, Glob, comandos de listagem).
2. **Evidência, não suposição.** Todo finding cita `arquivo:linha` (ou `arquivo:inicio-fim`) conferido com a numeração real do arquivo. Nunca estime números de linha.
3. **O projeto-alvo é o diretório atual** (onde o usuário invocou a skill). Ignore `.claude/`, dependências instaladas e artefatos (ver project-analysis §1).
4. **Preserve o contrato da API:** mesmos paths, métodos, códigos de status de sucesso e chaves JSON. Mudanças de contrato só são permitidas para eliminar um problema de segurança e devem ser listadas no resumo final (ver mvc-guidelines §6).
5. **Preserve o comando de start** detectado na Fase 1 (ex.: `python app.py`, `npm start`).
6. **Não mexa no índice do git:** nada de `git add`, `git rm`, `git mv`, `git commit` ou `git stash`. Apague/mova arquivos com comandos comuns (`rm`, `mv`) e deixe todas as mudanças **fora do staging** para revisão e commit humanos.
7. **Adapte-se ao contexto:** um monolito recebe camadas novas; um projeto já parcialmente organizado é *completado e corrigido*, sem reescrever o que já está bom.

---

## FASE 1 — Análise do projeto (somente leitura)

1. Leia `references/project-analysis.md`.
2. Liste os arquivos de código-fonte e conte linhas (§1).
3. Detecte linguagem, framework + versão, dependências, banco, tabelas, seed, entry point, porta e comando de start (§2-4).
4. Extraia o inventário completo de rotas (§5) e infira o domínio (§6).
5. Classifique a arquitetura atual e mapeie as responsabilidades de cada arquivo (§7).
6. **Imprima** o bloco `PHASE 1: PROJECT ANALYSIS` exatamente no formato do §8, seguido do mapa de responsabilidades e do inventário de rotas.

Prossiga direto para a Fase 2.

## FASE 2 — Auditoria (somente leitura)

1. Leia `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.
2. **Leia integralmente cada arquivo de código-fonte** listado na Fase 1. Para cada anti-pattern do catálogo, aplique os sinais de detecção (use `grep -n` para localizar e confirme lendo o trecho).
3. Verifique obrigatoriamente a seção **APIs deprecated** do catálogo contra as versões detectadas na Fase 1.
4. Para cada ocorrência confirmada, registre um finding: severidade (do catálogo, ajustável com justificativa), ID do anti-pattern, `arquivo:linhas`, descrição concreta do que o código faz, impacto e recomendação (com o ID do padrão do playbook).
   - Agrupe ocorrências do **mesmo** anti-pattern no mesmo arquivo em um finding com várias linhas; ocorrências em arquivos diferentes podem ser um finding com lista de locais.
   - Não reporte algo que você não consegue apontar no código.
5. Ordene CRITICAL → HIGH → MEDIUM → LOW e **imprima o relatório completo** exatamente no formato do template.
6. Termine com a pergunta abaixo e **PARE. Aguarde a resposta do usuário. Não chame nenhuma ferramenta de escrita.**

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- Resposta `n` (ou qualquer negativa): encerre informando que nenhum arquivo foi alterado.
- Resposta `y`: siga para a Fase 3.

## FASE 3 — Refatoração para MVC (após o "y")

Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`, depois execute na ordem:

1. **Registrar o relatório.** Salve o relatório da Fase 2, sem alterações, em `docs/audit-report.md` no projeto.
2. **Baseline.** Prepare o ambiente (ex.: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, `npm install`), rode o seed se necessário, suba a aplicação **em background** e chame cada rota do inventário com requisições válidas (use exemplos do README/`*.http` quando existirem). Registre método, path, status e chaves de topo do JSON numa tabela. Destrutivas por último. Derrube o processo ao final (`kill` pelo PID) e apague bancos locais gerados só pelo baseline (ex.: `*.db` ignorados pelo git) para que o seed rode de novo.
3. **Planejar.** Defina a estrutura-alvo a partir de mvc-guidelines §3-4, adaptada à stack e ao nível de organização atual. Imprima o mapeamento `arquivo antigo → arquivo(s) novo(s)`.
4. **Refatorar** aplicando os padrões do playbook para **cada finding** do relatório (use o ID PB-xx indicado). Ordem recomendada: config/segredos → camada de dados (models, SQL parametrizado, hash de senha) → controllers/services → views/rotas → error handling → composition root → limpeza (código morto, imports, arquivos antigos que foram totalmente migrados).
   - Se precisar de dependência nova, prefira stdlib ou algo já incluído no framework; se adicionar, atualize o manifesto.
   - Crie `.env.example` com todas as variáveis de configuração (sem valores secretos reais).
5. **Validar** (obrigatório — não declare sucesso sem executar):
   - a) Boot: suba a aplicação com o **comando de start original**; verifique que não há erros/tracebacks no log.
   - b) Endpoints: repita as mesmas requisições do baseline e compare status e chaves. Diferenças só são aceitas se forem mudanças de segurança intencionais (regra 4).
   - c) Anti-patterns: repita os greps de detecção dos findings CRITICAL/HIGH e confirme que não restam ocorrências.
   - d) Se algo falhar, corrija e valide de novo (até 3 ciclos); se ainda falhar, reporte com honestidade o que ficou pendente.
   - e) Derrube o servidor ao final.
6. **Relatório final.** Imprima o bloco abaixo e salve-o também em `docs/refactor-summary.md`:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios, sem dependências/artefatos>

## Findings addressed
<tabela: ID do finding | severidade | padrão aplicado (PB-xx) | status>

## Intentional contract changes
<lista (ou "None")>

## Validation
  ✓/✗ Application boots without errors (`<comando>`)
  ✓/✗ All endpoints respond correctly (<N>/<N> match baseline)
  ✓/✗ Zero CRITICAL/HIGH anti-patterns remaining
<tabela baseline vs. depois: método | path | status antes | status depois>
================================
```
