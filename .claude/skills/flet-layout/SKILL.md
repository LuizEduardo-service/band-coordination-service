# Skill: Flet Layout Review

## Trigger

Use when asked to:
- Reposition or reorganize UI elements
- Fix layout problems ("não está em padrão aceitável", "reorganizar", "posicionar")
- Review a Flet page for layout quality
- Audit spacing, hierarchy, or component misuse

## What This Skill Does

Reviews a Flet page against Material Design 3 conventions and the patterns established in this project. Outputs a prioritized list of layout issues and applies fixes.

---

## Layout Hierarchy (Material Design 3)

Reference: https://m3.material.io/foundations/layout/understanding-layout/overview

### Canonical structure for a config/management page

```
AppBar          ← navigation + title + user action
  └─ title      ← page context (not app name)
  └─ leading    ← back button always present
  └─ actions    ← user chip last; secondary actions before it

PageContainer   ← padding=24, expand=True
  └─ Column(expand=True, spacing=SPACING['md'])
       ├─ Page-level messages (error_msg, success_msg)  ← top, always visible
       ├─ SectionTitle('Primary section', trailing=secondary_action_btn)
       ├─ Primary content area  ← SurfaceCard(list, expand=1) scrollable
       ├─ SectionTitle('Secondary section')  ← below primary content
       └─ Secondary form/panel  ← SurfaceCard, no expand
```

### Priority order of content blocks

1. **Status messages** (error/success) — always first, always visible
2. **Primary list / read content** — expanded, scrollable, most screen space
3. **Primary action form** (add/create) — below list, compact
4. **Rare/secondary actions** → Dialog or BottomSheet, never inline

---

## Component Conventions (this project)

### When to use each component

| Need | Component | Notes |
|------|-----------|-------|
| Page wrapper | `PageContainer` | Always, padding=24 |
| Content group | `SurfaceCard` | With title inside if standalone |
| Section header | `SectionTitle(text, trailing=btn)` | Max one trailing control |
| Empty state | `EmptyState(msg, icon=...)` | Centered, icon + text |
| Input field | `FormField(label, width=None)` | width=None = full width inside column |
| Dropdown | `StyledDropdown(label, opts, width=None)` | width=None for responsive |
| Primary action | `PrimaryButton` or `ft.FilledButton` | One per form |
| Secondary action | `ft.FilledTonalButton` | Positive, non-destructive secondary |
| Destructive action | `ft.TextButton` | Small, no fill |
| Rare action | `ft.OutlinedButton` | Opens dialog |

### Width discipline

- **Never hardcode widths** on form fields inside a Column — use `width=None` (expand to parent)
- `width=300` or `width=420` only for standalone centered forms (login, register)
- `ft.Row([field], expand=True)` if field needs to stretch

### Spacing rules

```
Between cards/sections : SPACING['md'] = 12  (Column spacing)
Inside card            : SPACING['md'] = 12  (Column spacing)
Between chips/buttons  : SPACING['sm'] = 8
Between icon and label : SPACING['xs'] = 4
Card padding           : SPACING['md'] or SPACING['sm'] for compact lists
Page padding           : 24 (PageContainer default)
```

### Dialog vs BottomSheet

| Use Dialog (AlertDialog) | Use BottomSheet |
|--------------------------|-----------------|
| Action requires form input | Read-only detail view |
| Confirmation needed | Quick reference |
| Rare/secondary create action | Song detail, event summary |
| User search + invite flow | — |

**Dialog pattern:**
```python
dlg = ft.AlertDialog(
    modal=True,
    title=ft.Text('Action Title'),
    content=ft.Container(
        content=ft.Column([...], scroll=ft.ScrollMode.AUTO, spacing=SPACING['md']),
        width=400,
        height=480,  # constrain so dialog doesn't overflow
    ),
    actions=[
        ft.TextButton('Cancelar', on_click=close_dlg),
        ft.FilledButton('Confirmar', on_click=confirm_action),
    ],
    actions_alignment=ft.MainAxisAlignment.END,
)

def open_dlg(_):
    page.dialog = dlg
    dlg.open = True
    page.update()

def close_dlg(_):
    dlg.open = False
    page.update()
```

**BottomSheet pattern:**
```python
sheet_body = ft.Column(spacing=SPACING['md'], tight=True)
sheet = ft.BottomSheet(
    content=ft.Container(content=sheet_body, padding=SPACING['lg']),
    open=False,
)
page.overlay.append(sheet)

def open_sheet(data):
    sheet_body.controls.clear()
    # populate
    sheet.open = True
    page.update()
```

---

## Common Anti-Patterns to Fix

| Anti-pattern | Fix |
|---|---|
| Inline form for rare action (invite, suggest) | Move to AlertDialog triggered by OutlinedButton |
| Hardcoded width on fields inside Column | Set `width=None` |
| Secondary panel above primary list | Primary list first, secondary forms below |
| Scrollable Column inside scrollable Column | Inner list: `scroll=AUTO` inside SurfaceCard(expand=1); outer Column: no scroll |
| Loop variable shadowing outer scope (`slug`) | Rename loop var (`inst_slug`, `opt`) |
| Accessing `member['membership']` without guard | Guard: `(member.get('membership') or {}).get('user') or {}` |
| `page.overlay.append` called inside loop | Append once outside, reuse |

---

## Review Checklist

Run through this when reviewing a Flet page:

- [ ] `PageContainer` wraps all content
- [ ] `Column(expand=True, spacing=SPACING['md'])` at root (no scroll on outer if inner list expands)
- [ ] Status messages (error/success) before first SectionTitle
- [ ] Primary content in `SurfaceCard(..., expand=1)` to fill space
- [ ] Rare actions in Dialog, not inline panels
- [ ] Field widths: `None` inside columns, fixed only for centered forms
- [ ] Spacing tokens used, no literal integers outside theme.py
- [ ] `loading = ft.ProgressRing(visible=True)` hidden in `finally` block
- [ ] AppBar `leading` = back button, `actions` ends with `app_bar_user_row`
- [ ] No loop variable name collision with outer scope

---

## References

- Material Design 3 Layout: https://m3.material.io/foundations/layout/understanding-layout/overview
- Material Design 3 Components: https://m3.material.io/components
- Flet Controls: https://flet.dev/docs/controls/
- Flet Layout: https://flet.dev/docs/controls/row/ · /column/ · /container/
- Flet Dialogs: https://flet.dev/docs/controls/alertdialog/
- Flet BottomSheet: https://flet.dev/docs/controls/bottomsheet/
