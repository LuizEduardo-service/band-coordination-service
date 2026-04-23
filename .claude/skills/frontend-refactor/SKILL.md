# Frontend Refactor Skill

## Summary
Analisa estrutura Flet, propõe componentização por padrão (reusable containers, styled cards, themed buttons), refatora páginas usando componentes reutilizáveis.

## Invoke
```
/frontend-refactor
```

## What it does

1. **Explore** — lê `pages/*.py`, identifica UI patterns repetidos (cards, buttons, containers)
2. **Propose** — cria `components/` module com componentes base (StyledCard, PrimaryButton, Header, FormField, etc)
3. **Refactor** — reescreve pages para usar novos componentes, aplica tema consistente, reduz duplicação
4. **Theme** — define palette central (`theme.py`): cores, spacing, typography

## Output
- `frontend/components/` — componentes reutilizáveis
- `frontend/theme.py` — config de tema global
- `pages/` — refatoradas para usar componentes
- Relatório de mudanças

## Files affected
- Creates: `frontend/components/__init__.py`, `frontend/components/styled.py`, `frontend/theme.py`
- Modifies: `frontend/pages/login_page.py`, `frontend/pages/dashboard_page.py`

## Notes
- Preserva funcionalidade existente (async, event handlers)
- Segue SOLID (componentes são SRP)
- Mantém nomes de funções `build_*_page()` para compatibilidade
