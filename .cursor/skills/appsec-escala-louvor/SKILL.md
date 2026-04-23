---
name: appsec-escala-louvor
description: >-
  Auditoria e endurecimento de segurança para Escala Louvor (Django/DRF + Flet).
  Use ao revisar permissões, auth/JWT, multi-tenant, configuração, dependências,
  cliente HTTP, sessão/tokens, telas Flet (inputs, exibição de dados, erros),
  CORS/CSRF, ou quando o usuário pedir segurança, OWASP, auditoria, vulnerabilidade,
  hardening, pentest leve, revisão de API ou frontend.
---

# Segurança da aplicação (Escala Louvor)

Atue como revisor de **segurança pragmático**: identificar fragilidades, **corrigir com mudança mínima** e boas práticas do stack (Django, DRF, Flet, httpx). Base legal do projeto: `CLAUDE.md` (OWASP e multi-tenancy).

## Antes de alterar código

1. Ler `CLAUDE.md` (OWASP, camadas, A01).
2. Confirmar contexto: **produção** vs **desenvolvimento** (o que é aceitável em dev pode ser bloqueador em prod).
3. Localizar settings: `backend/**/settings/*.py` (ou equivalente no repo) para `DEBUG`, `ALLOWED_HOSTS`, `CORS`, `SECRET_KEY`, JWT.

## Mapa rápido OWASP → este repositório

| Risco | O que verificar | Correção típica |
|-------|-----------------|-----------------|
| **A01 Access control** | ViewSet sem `permission_classes`; queryset sem filtro por `group`; confiar em `group_id` do body/query | `IsGroupMember` / `IsGroupAdmin`; resolver grupo pela URL; `get_queryset()` sempre escopado |
| **A02 Crypto / secrets** | `SECRET_KEY` default; JWT sem rotação/alinhado à política; senha em texto puro | env vars; `set_password`; revisar `SIMPLE_JWT` (ou equivalente) vs `CLAUDE.md` |
| **A03 Injection** | SQL raw; `extra()` inseguro; concatenar strings em query | ORM `.filter()`; validação em serializers |
| **A04 Insecure design** | “Admin” genérico; expor IDs de outros tenants | permissões granulares; 403/404 consistentes |
| **A05 Misconfiguration** | `DEBUG=True` em prod; `ALLOWED_HOSTS=*`; CORS aberto | `--deploy` checks; whitelist CORS; hardening settings |
| **A07 Auth failures** | brute force ilimitado (se crítico); refresh longo demais | throttling/rate limit onde couber; política de token documentada |
| **A08 Data integrity** | deserialização insegura de dados não confiáveis | JSON via DRF; evitar `pickle` de entrada |
| **A09 Logging** | logar tokens/senhas | mascarar; logs sem PII sensível |
| **A10 SSRF** | URL de usuário passada a `httpx`/`requests` no backend | allowlist de hosts ou não buscar URL arbitrária |
| **UI / cliente (Flet)** | Só validação na UI; mensagem de erro crua da API; token/senha em `print`/log ou em widget de debug | **Backend continua fonte da verdade**; sanitizar/limitar mensagem ao usuário; nunca logar credenciais; ver checklist frontend abaixo |

**Frontend (Flet) — resumo:** tokens em `page.session` (`AppState`); validar inputs **antes** de enviar à API (reforço UX — **não** substitui validação no DRF); não embutir **segredos** no cliente; `APIClient.BASE_URL` configurável por ambiente em produção. Cruzar com `.cursor/skills/flet-frontend-validate/SKILL.md` para compatibilidade de API Flet e build.

## Checklist backend (DRF)

- [ ] Cada endpoint novo/alterado: **permission class** explícita (não só default global ambíguo).
- [ ] `get_queryset` / `get_object`: escopo por **grupo** e **membership**, alinhado aos padrões existentes.
- [ ] Serializers: validação de entrada; não persistir campos que o cliente não deveria controlar (ex.: `group` arbitrário) sem checagem.
- [ ] Uploads/arquivos (se houver): tipo/tamanho; storage seguro.
- [ ] Erros: não vazar stack trace em prod; mensagens úteis sem expor dados internos.

## Checklist frontend (Flet) — fragilidades comuns

### Auth, sessão e transporte

- [ ] Nenhum segredo (API keys de terceiros, chave de assinatura JWT, senhas de serviço) no código do `frontend/`.
- [ ] `AppState` / `page.session`: `clear()` no logout; após 401, não manter UI como “logado” (alinhado ao `APIClient`).
- [ ] Chamadas HTTP: manter `verify=True` (padrão httpx) em produção; não desabilitar TLS por conveniência.
- [ ] Base URL da API: evitar host fixo só de dev em builds de produção; variável de ambiente ou config injetada no build.

### Entrada do usuário e dados na tela

- [ ] **Validação só no Flet não basta** — ocultar botão ou campo não protege API; garantir que o backend nega a ação (A01).
- [ ] Normalizar/validar entrada antes de `post`/`patch` (vazio, tamanho, caracteres) para reduzir 400 e abuso; regras fortes no serializer.
- [ ] Evitar `eval`, `exec`, `pickle.loads` ou equivalente com dados vindos da API ou digitados pelo usuário.
- [ ] Se exibir conteúdo rico no futuro (HTML/Markdown de usuário): tratar como não confiável; preferir texto plano ou sanitização explícita (política do produto).

### Erros, logs e vazamento de informação

- [ ] `APIError` / `resp.text`: não mostrar ao usuário corpo bruto de erro interno, stack traces ou IDs internos que facilitem enumeração.
- [ ] `print`, `logging` ou arquivos de debug no cliente: não registrar `token`, `refresh_token`, senha ou PII desnecessária.
- [ ] Mensagens de validação amigáveis sem confirmar existência de recurso de outro tenant (ex.: “e-mail não encontrado” vs “credenciais inválidas” — alinhar ao desenho de produto).

### Arquivos e permissões de UI

- [ ] `FilePicker` / upload: validar tipo e tamanho esperado no backend; na UI, só enviar o necessário.
- [ ] Não assumir que “rota Flet” protege dado: qualquer tela pode ser montada se o estado local mentir — **sempre** depender da API autenticada/autorizada.

### Revisão dirigida por arquivo

| Área | Arquivos típicos | Foco |
|------|------------------|------|
| Transporte / erros | `frontend/api/client.py`, `frontend/api/*.py` | TLS, headers, tratamento 401/403, vazamento em mensagens |
| Sessão | `frontend/state/app_state.py` | persistência em session, clear |
| Fluxo auth | `frontend/pages/login_page.py`, `main.py` | não persistir senha em claro; rota login vs autenticado |
| Formulários | `frontend/pages/*.py`, `frontend/components/*.py` | validação básica, não confiar só na UI |

Após alterações relevantes no frontend, quando possível: `cd frontend && poetry run python -m compileall components pages main.py -q` (como no skill Flet).

## Configuração e deploy

- `python manage.py check --deploy` (com `DJANGO_SETTINGS_MODULE` de produção quando aplicável).
- Dependências: `pip audit` ou `poetry audit` no backend; atualizar patches de segurança.
- CORS: origens explícitas em produção (`CLAUDE.md`).
- HTTPS em produção; cookies/session — se no futuro usar cookies, flags `Secure`/`HttpOnly` conforme modelo.

## Ferramentas (opcional)

```bash
# Backend — checagens de deploy (ajustar DJANGO_SETTINGS_MODULE se necessário)
cd backend && poetry run python manage.py check --deploy

# Dependências vulneráveis — usar o que o time adotar (ex.: pip-audit no venv/poetry)
# Ver também CLAUDE.md (A06) e pipeline de CI
```

## Fluxo de resposta ao usuário

1. **Escopo** da revisão (arquivos/área).
2. **Achados** por severidade (crítico / alto / médio / baixo) com **arquivo ou padrão** (sem alarmismo).
3. **Correções propostas** ou aplicadas: pequenas, testáveis, alinhadas a `CLAUDE.md`.
4. **Regressão**: o que rodar (testes existentes, smoke manual).

## Princípios ao corrigir

- Preferir **padrões já usados** no repo (permissions, serializers, `APIClient`).
- **Não** introduzir framework de segurança pesado sem necessidade.
- Mudança que altera comportamento de API ou auth: sugerir/atualizar **testes** (401/403/404, tenant).
