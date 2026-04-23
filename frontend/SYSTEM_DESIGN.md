# Frontend System Design — Escala Louvor

> Referência canônica para o frontend Flet/Material 3.
> Consultar antes de editar componentes existentes ou criar novos.

---

## Stack

- **Flet** (Python wrapper de Flutter) — Material 3
- **Seed color:** `ft.colors.INDIGO_700`
- **Theme:** `use_material3=True`, `visual_density=COMFORTABLE`
- Arquivo de tokens: `frontend/theme.py`
- Componentes reutilizáveis: `frontend/components/styled.py`

---

## Design Tokens (`frontend/theme.py`)

### Espaçamento — `SPACING`
| Token | px |
|---|---|
| `xs` | 4 |
| `sm` | 8 |
| `md` | 12 |
| `lg` | 24 |
| `xl` | 40 |

### Tipografia — `FONT_SIZES`
| Token | px | Uso |
|---|---|---|
| `title` | 28 | Títulos de tela |
| `subtitle` | 18 | Subtítulos / nome do grupo |
| `label` | 14 | SectionTitle, labels |
| `body` | 12 | Texto secundário, subtitles |

### Ícones — `ICON_SIZES`
| Token | px | Uso |
|---|---|---|
| `sm` | 20 | Ícones compactos (lista, chips) |
| `md` | 24 | Padrão M3 (ListTile leading, AppBar) |
| `lg` | 40 | EmptyState, avatares médios |
| `hero` | 56 | Ícone principal de tela (login/register) |

### Cores — `COLORS`
| Token | Valor M3 | Uso |
|---|---|---|
| `primary` | `PRIMARY` | CTAs, ícones ativos |
| `error` | `ERROR` | Destrutivo, validação |
| `secondary` | `ON_SURFACE_VARIANT` | Texto secundário, ícones inativos |
| `background` | `SURFACE` | Fundo de página |
| `surface_container` | `SURFACE_VARIANT` | Cards, inputs, avatares |
| `outline` | `OUTLINE_VARIANT` | Bordas de cards/campos |
| `success` | `TERTIARY` | Confirmações, sucesso |
| `transparent` | `TRANSPARENT` | Divisórias invisíveis |

### Raios de borda
| Token | px | Uso |
|---|---|---|
| `RADIUS_FIELD` | 12 | TextField, Dropdown |
| `RADIUS_CARD` | 16 | ft.Card |
| `RADIUS_SURFACE` | 16 | SurfaceCard (Container) |

### Outros tokens
| Token | Valor | Uso |
|---|---|---|
| `CARD_ELEVATION` | 1.5 | Elevação padrão de cards |
| `MIN_TOUCH_TARGET` | 48 | Altura mínima de botões clicáveis |
| `SAFE_BOTTOM` | 24 | Padding extra inferior (nav bar sistema) |
| `FORM_MAX_WIDTH` | 480 | Largura máxima de formulários centrados |
| `BREAKPOINT_MOBILE` | 600 | Largura para troca de layout responsivo |

---

## Componentes (`frontend/components/styled.py`)

### `ErrorText(message='') → ft.Text`
Texto de erro invisível por padrão. Mutável via `.value` e `.visible`.
```python
err = ErrorText()
err.value = 'Algo deu errado'
err.visible = True
page.update()
```

### `FormField(label, password=False, width=None, autofocus=False, dense=False) → ft.TextField`
- Sem `width` → `expand=True` (preenche pai)
- `filled=True`, `border_radius=RADIUS_FIELD`
- Usar `dense=True` dentro de dialogs compactos

### `PrimaryButton(label, width=None, *, visible=None, expand=True) → ft.FilledButton`
- `height=MIN_TOUCH_TARGET` sempre
- Sem `width` + `expand=True` → expande horizontalmente (padrão para formulários)
- `expand=False` para botões em tabs, cards, barras de ações de dialog

### `DangerButton(label, *, expand=False) → ft.FilledButton`
Botão destrutivo pré-estilizado (fundo `COLORS['error']`, texto branco).
```python
btn = DangerButton('Excluir')
btn.on_click = handle_delete
```

### `SectionTitle(text, *, trailing=None) → ft.Row`
Cabeçalho de seção. `trailing` aceita qualquer Control (ex: botão, dropdown filtro).

### `EmptyState(message, *, icon=ft.icons.INBOX_OUTLINED) → ft.Container`
Estado vazio centralizado com ícone `ICON_SIZES['lg']`.

### `SurfaceCard(content, *, padding=SPACING['md'], width=None, expand=None) → ft.Container`
Container com `SURFACE_VARIANT` + borda outline + `RADIUS_SURFACE`.
- **Não** usar `expand=1` dentro de `Column(scroll=AUTO)` — causa colapso de layout.

### `CenteredForm(content) → ft.Container`
Centraliza formulário com `max-width=FORM_MAX_WIDTH`. Usar em login/register.

### `PageContainer(content, padding=24) → ft.Container`
Wrapper de página com padding lateral + `SAFE_BOTTOM` inferior. Sempre o último wrapper antes do `ft.View`.

### `StyledDropdown(label, options, width=None) → ft.Dropdown`
- Sem `width` → `expand=True`
- Para caps de largura, envolver em `ft.Container(width=N)`

### `Spacer(height=None) → ft.Divider`
Divisória invisível para espaçamento vertical entre seções.

---

## Padrão de Página

```python
def build_<name>_page(page: ft.Page, state: AppState, ...) -> ft.View:
    # 1. Controles de estado (ErrorText, ProgressRing, Column de lista)
    # 2. Handlers async def (APIClient, try/except APIError as ex: .message)
    # 3. Dialogs (AlertDialog + helpers _open_dialog/_close_dialog)
    # 4. Builders de lista (_build_card, _build_row)
    # 5. page.run_task(load_fn) — carga inicial
    # 6. Layout (Column/content com scroll se necessário)
    # 7. return ft.View(route, [AppBar, PageContainer(content)])
```

**Regras:**
- Toda chamada API: `async def` + `await` + `except APIError as ex: err.value = ex.message`
- Nunca `page.update()` dentro de loop — sempre no final do handler
- `asyncio.gather()` para cargas paralelas independentes
- Estado: `AppState` + `page.session`; nunca estado global

---

## Padrão de AlertDialog

```python
ft.AlertDialog(
    modal=True,
    title=ft.Text('...'),
    content=ft.Container(
        content=ft.Column(
            [...campos...],
            spacing=SPACING['sm'],
            tight=True,
        ),
        padding=ft.padding.only(top=SPACING['sm']),
    ),
    actions=[...],  # lista PLANA — nunca ft.Row dentro de actions
    actions_alignment=ft.MainAxisAlignment.END,
)
```

### Hierarquia de botões em `actions` (M3)
| Posição | Tipo | Uso |
|---|---|---|
| 1º (esquerda) | `ft.TextButton` | Cancelar / Fechar |
| 2º (opcional) | `ft.TextButton(style=ButtonStyle(color=COLORS['error']))` | Ação destrutiva secundária (navega para confirm) |
| 3º (opcional) | `ft.FilledTonalButton` | Ação secundária positiva |
| Último (direita) | `PrimaryButton(expand=False)` | Ação principal (salvar, enviar) |

**Regras críticas:**
- `actions` = lista plana de controls — Flet alinha como Row internamente com `actions_alignment`
- **Nunca** embrulhar em `ft.Row` ou `ft.Column` dentro de `actions`
- `PrimaryButton` com `expand=False` dentro de dialog actions
- Dialog de confirmação de exclusão: usar `DangerButton` como botão principal

### Helpers padrão (copiar para cada página)
```python
def _open_dialog(dlg: ft.AlertDialog) -> None:
    page.dialog = dlg
    dlg.open = True
    page.update()

def _close_dialog(dlg: ft.AlertDialog) -> None:
    dlg.open = False
    page.update()
```

---

## Padrão de Cards de Lista

```python
ft.Card(
    elevation=CARD_ELEVATION,
    content=ft.Container(
        content=ft.ListTile(
            leading=<avatar_widget ou ft.Icon>,
            title=ft.Text(..., weight=ft.FontWeight.W_600),
            subtitle=ft.Text(..., color=COLORS['secondary'], size=FONT_SIZES['body']),
            trailing=ft.Icon(ft.icons.CHEVRON_RIGHT_ROUNDED, color=COLORS['secondary']),
            on_click=on_tap,
        ),
        border_radius=RADIUS_CARD,
    ),
)
```

### Avatar circular em cards
```python
avatar_url = group.get('avatar_url')
leading = ft.Container(
    width=40, height=40, border_radius=20,
    bgcolor=COLORS['surface_container'],
    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    content=ft.Image(src=avatar_url, width=40, height=40, fit=ft.ImageFit.COVER)
            if avatar_url
            else ft.Icon(ft.icons.GROUP_WORK_OUTLINED, size=ICON_SIZES['sm'], color=COLORS['primary']),
    alignment=ft.alignment.center,
)
```

---

## Padrão de Carregamento

```python
loading = ft.ProgressRing(visible=True)

async def load_data():
    loading.visible = True
    page.update()
    try:
        data = await client.get(...)
        # popular lista/controles
    except APIError as ex:
        error_msg.value = ex.message
        error_msg.visible = True
    except Exception:
        error_msg.value = 'Erro ao carregar.'
        error_msg.visible = True
    finally:
        loading.visible = False
        page.update()

page.run_task(load_data)
```

---

## Padrão de Upload de Arquivo

```python
file_picker = ft.FilePicker(on_result=on_file_picked)
page.overlay.append(file_picker)

def on_file_picked(e: ft.FilePickerResultEvent) -> None:
    if not e.files:
        return
    raw = open(e.files[0].path, 'rb').read()
    # preview base64:
    b64 = base64.b64encode(raw).decode()
    preview.content = ft.Image(src=f'data:image/jpeg;base64,{b64}', fit=ft.ImageFit.COVER)
    page.update()

# upload via patch_multipart:
updated = await client.patch_multipart(
    f'/groups/{slug}/',
    files={'avatar': ('avatar.jpg', raw, 'image/jpeg')},
    data={'name': name},
)
```

---

## Anti-padrões (não fazer)

| ❌ Errado | ✅ Correto |
|---|---|
| `ft.Row([...])` dentro de `AlertDialog.actions` | Lista plana em `actions` |
| `width=300` fixo em FormField/Button | `expand=True` (padrão do componente) |
| `ex.detail` em APIError | `ex.message` (property) |
| `SurfaceCard(expand=1)` em `Column(scroll=AUTO)` | Sem `expand` em Column scrollável |
| `page.update()` dentro de loop | Uma única chamada ao final do handler |
| `Event.objects.all()` no backend | Sempre filtrar por `group=self.get_group()` |
| Cores inline (`ft.colors.RED`) | `COLORS['error']` do theme.py |
| Tamanhos de ícone hardcoded (`size=26`) | `ICON_SIZES['md']` do theme.py |
| `ft.ButtonStyle(bgcolor=COLORS['error'], ...)` inline | `DangerButton(label)` do styled.py |
