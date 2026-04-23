---
name: flet-frontend-validate
description: >-
  Validates Flet frontend code for API compatibility, layout patterns, and
  escala-louvor conventions. Use when editing frontend/pages or components,
  debugging Flet AttributeError, reviewing UI changes, or verifying the app before
  release. Triggers: Flet, frontend, validação UI, AppBar, rota, compile error.
---

# Validação de frontend Flet (expert)

Aplica uma revisão sistemática como especialista em **Flet**, alinhada à versão declarada em `frontend/pyproject.toml` e aos padrões já usados neste repositório.

## Antes de alterar código

1. Ler `frontend/pyproject.toml` e anotar a versão de `flet` (ex.: `^0.21`).
2. Se a doc online divergir da versão fixada, **prevalece a versão instalada**; confirmar com `poetry run python -c "import flet as ft; print(ft.__version__)"` no diretório `frontend/`.
3. Consultar links oficiais em [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).

## Checklist de validação (executar na ordem)

### 1. Sintaxe e importação

```bash
cd frontend && poetry run python -m compileall components pages main.py -q
```

Falha aqui impede subir o app; corrigir antes de qualquer revisão de UI.

### 2. Padrões que quebram neste projeto (Flet 0.21.x)

| Problema | Sintoma | Correção típica |
|----------|---------|------------------|
| API inexistente | `AttributeError: module 'flet' has no attribute 'X'` | Conferir se `X` existe na versão instalada; ver [examples/](examples/) |
| `ft.Wrap` | idem | Usar `ft.Row(..., wrap=True)` ou `ft.Column` |
| `ft.InkWell` | idem | `ft.GestureDetector` + `on_tap`; tooltip com `ft.Tooltip` |
| Controles custom (`PrimaryButton`, etc.) | `unexpected keyword argument` | Estender o wrapper em `components/styled.py` ou repassar `**kwargs` ao controle Flet base |

### 3. Arquitetura do app (este repositório)

- **Rotas:** `frontend/main.py` — ordem das condições importa (rotas mais específicas antes das genéricas).
- **Estado:** `state.app_state.AppState`; sessão (`token`, `user`).
- **API:** `frontend/api/` + `APIClient(state, page)`.
- **Tema:** `theme.py` (`COLORS`, `SPACING`, …); preferir tokens a cores literais espalhadas.
- **Componentes:** `components/styled.py`, `components/app_bar_user.py`, etc.

### 4. UX e controles

- **AppBar:** `actions` recebe lista de controles; ordem costuma ser chip do usuário → outras ações.
- **Async:** handlers que chamam API devem ser `async def` e usar `await`; disparar com `page.run_task(...)` quando necessário.
- **Atualização:** após mudar estado de controles, `page.update()` quando o fluxo exigir.

### 5. Verificação automatizada de padrões (opcional)

Do root do repositório:

```bash
python .cursor/skills/flet-frontend-validate/scripts/check_flet_patterns.py
```

Lista usos suspeitos (`Wrap`, `InkWell`, …) em `frontend/`. Ajustar falsos positivos no script se aparecerem nomes legítimos.

## Formato do relatório ao usuário

Ao validar sem implementar correção, entregar:

1. **Versão Flet** (pyproject + `ft.__version__` se tiver sido checado).
2. **Resultado** de `compileall` (ok / erros com arquivo e linha).
3. **Achados** do script de padrões (se rodado).
4. **Riscos** (rotas, permissões, estado desatualizado na UI).
5. **Links** relevantes de [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) para o problema.

## Recursos no repositório

- [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) — documentação oficial e comunidade.
- [examples/](examples/) — trechos mínimos alinhados às versões antigas do SDK quando a doc mostra APIs mais novas.

## Notas de versão

Quando o projeto **atualizar** o Flet, revisar este skill: reexecutar o script, atualizar a tabela de “padrões que quebram” e os exemplos conforme o changelog do Flet.
