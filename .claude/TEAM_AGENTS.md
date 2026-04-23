# Team Agents — Escala Louvor

Três agentes especializados para paralelizar desenvolvimento de novas funcionalidades.

## Frontend Agent (telas Flet)
**Responsável por:** Criação e evolução de telas, componentes Flet, UI/UX e styling em `frontend/`.

**Contrato persistente (Cursor):** `.cursor/rules/flet-screen-agent.mdc` — aplicado ao editar `frontend/**/*.py`. Define padrão `build_*_page`, rotas em `main.py`, `AppState`, `APIClient`, tema, SOLID pragmático, componentização e notas de performance.

**Validação:** seguir checklist em `.cursor/skills/flet-frontend-validate/SKILL.md` (`compileall`, padrões que quebram no Flet fixado no `pyproject`).

**Especialidades:**
- Páginas com `build_<nome>_page(...) -> ft.View` alinhadas a `pages/*.py` existentes
- Componentes reutilizáveis em `components/` (evitar duplicar colunas/forms inteiros)
- Async/await em handlers que chamam API; `page.run_task` quando necessário
- Integração via `api/*` + `APIClient(state, page)`; tratamento de `APIError`
- Tokens de `theme.py` e controles de `styled.py` / `app_bar_user.py`

**Constraints:** SOLID sem over-engineering; sem camadas abstratas desnecessárias; performance consciente (updates mínimos, listas paginadas quando couber)

**Invoke:** Com arquivos do frontend abertos ou mencionando Flet/`frontend/`, a regra acima entra no contexto. Para tarefa isolada: `Agent(subagent_type="general-purpose")` com instrução explícita para seguir `flet-screen-agent.mdc` e o skill de validação.

---

## Backend Agent (Django / DRF)
**Responsável por:** APIs, modelos, serializers, permissões, autenticação e regras de domínio no backend.

**Contrato persistente (Cursor):** `.cursor/rules/backend-agent.mdc` — aplicado ao editar `backend/**/*.py`. Prioriza **clareza**, **clean code básico**, **SOLID pragmático** e **separação de camadas quando fizer sentido**, sem over-engineering (sem serviço/repositório “por padrão” se ViewSet + queryset já ficam legíveis).

**Alinhamento:** `CLAUDE.md` — camadas (models ↑ serializers ↑ views), OWASP **A01** (queries escopadas por `Group`, permissões, não confiar em `group_id` solto), testes para mudanças de API.

**Especialidades:**
- Django models, DRF ViewSets, serializers com validação clara
- Permission classes granulares (`IsGroupMember`, `IsGroupAdmin`, …)
- JWT / autenticação conforme o app já implementa
- Testes com `APITestCase` (ou padrão do repositório)
- Multi-tenancy via `Group` e membership

**Constraints:** Código legível primeiro; extrair helper/serviço só com ganho real; manter dependências de camada corretas (model não importa view)

**Invoke:** Com arquivos do `backend/` abertos ou mencionando API Django/DRF, a regra entra no contexto. Tarefa isolada: `Agent(subagent_type="general-purpose")` com instrução para seguir `backend-agent.mdc` e `CLAUDE.md`.

---

## Security Agent (OWASP / hardening)
**Responsável por:** Revisar e corrigir fragilidades (acesso, auth, config, dependências, cliente HTTP, sessão), com boas práticas e diff mínimo.

**Skill (fonte da verdade):** `.cursor/skills/appsec-escala-louvor/SKILL.md` — checklist OWASP alinhado ao repo, fluxo de relatório e comandos (`manage.py check --deploy`, auditoria de dependências).

**Regra Cursor:** `.cursor/rules/appsec-agent.mdc` — ao editar `backend/**/*.py` ou `frontend/**/*.py` (API, sessão, páginas, componentes), priorizar o skill + `CLAUDE.md`.

**Invoke:** Mencionar segurança, OWASP, auditoria ou abrir arquivos cobertos pela regra; para Docker/settings/CI, pedir explicitamente o skill na conversa.

---

## QA Agent
**Responsável por:** Testes, validação end-to-end, relatórios

**Especialidades:**
- Testes de integração (login → feature → logout)
- Cobertura de edge cases (401, 403, 400, 200)
- Relatório de testes
- Verificar funcionalidade preservada
- Performance check

**Constraints:** Testes devem passar, sem regressions

**Invoke:** Via Agent(subagent_type="general-purpose") com contexto QA

---

## Workflow (Features + Config Pages)

### 1. Nova Funcionalidade
```
1. Frontend Agent: cria página Flet + componentes
2. Backend Agent: cria API + modelos + permissões
3. (Opcional) Security Agent: revisa permissões, escopo por grupo, auth/sessão
4. QA Agent: testa integração, valida, gera relatório
```

### 2. Config Pages (Initial Setup)
Telas para cadastrar dados iniciais:
- `ConfigGroupsPage` — criar grupo
- `ConfigMembersPage` — adicionar membros ao grupo
- `ConfigEventsPage` — criar eventos
- `ConfigSongsPage` — adicionar músicas ao repertório

---

## Invoke Pattern (Paralelo)

```
Agent 1: frontend-agent
  - cria `frontend/pages/config_*.py`
  - cria componentes em `frontend/components/`
  
Agent 2: backend-agent  
  - cria viewsets `/api/v1/config/*`
  - cria modelos/serializers
  - cria testes
  
Agent 3: qa-agent
  - testa frontend + backend integrados
  - gera relatório de cobertura
```

Usar múltiplos Agent() calls em paralelo (no mesmo message) para executar simultaneamente.

---

## Example Task

**Tarefa: "Add Config Pages para criar Grupos"**

Fase 1 — Paralelo (3 agents):
- Frontend: `ConfigGroupsPage(page, state)` com form para nome+descrição
- Backend: `POST /api/v1/groups/` com create + validação
- QA: teste 401 unauthenticated, 201 admin create, 403 member cannot create

Fase 2 — Integração:
- QA reintegra frontend+backend
- Frontend chama APIClient.post('/groups/', data)
- Backend persiste + retorna grupo criado
- QA valida full flow

---

## Setup

Não requer config file. Use comando:
```bash
# Para 1 funcionalidade com 3 agentes paralelos:
# User invoca manualmente via Agent(subagent_type=...)
# Ou coordinator task que spawna 3 agents

# Exemplo em conversa:
/start-feature "Config Grupos"
# → spawna 3 agentes, cada um trabalhando sua parte
```

---

## Notes

- Cada agent trabalha **isolado** (não interfere nos outros)
- Todos focam em **SOLID + Clean Arch + OWASP**
- QA é blocker: sem testes verdes, não merge
- Paralelização economiza tempo (3x mais rápido que sequencial)
