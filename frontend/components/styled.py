import flet as ft
from theme import COLORS, SPACING, FONT_SIZES, RADIUS_FIELD, RADIUS_SURFACE, CARD_ELEVATION, outline_border


def ErrorText(message: str = '') -> ft.Text:
    return ft.Text(message, color=COLORS['error'], visible=False)


def FormField(
    label: str,
    password: bool = False,
    width: int = 300,
    autofocus: bool = False,
    dense: bool = False,
) -> ft.TextField:
    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=password,
        width=width,
        autofocus=autofocus,
        filled=True,
        dense=dense,
        border_radius=RADIUS_FIELD,
    )


def PrimaryButton(
    label: str,
    width: int | None = 300,
    *,
    visible: bool | None = None,
) -> ft.FilledButton:
    kwargs: dict = {}
    if width is not None:
        kwargs['width'] = width
    if visible is not None:
        kwargs['visible'] = visible
    return ft.FilledButton(label, **kwargs)


def Spacer(height: int = None) -> ft.Divider:
    return ft.Divider(height=height or SPACING['md'], color=COLORS['transparent'])


def SectionTitle(text: str, *, trailing: ft.Control | None = None) -> ft.Row:
    title = ft.Text(
        text,
        size=FONT_SIZES['label'],
        weight=ft.FontWeight.W_600,
    )
    if trailing is None:
        return ft.Row([title])
    return ft.Row(
        [title, trailing],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def EmptyState(message: str, *, icon: str = ft.icons.INBOX_OUTLINED) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, size=40, color=COLORS['secondary']),
                ft.Text(message, color=COLORS['secondary'], text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACING['sm'],
        ),
        padding=SPACING['lg'],
        alignment=ft.alignment.center,
    )


def SurfaceCard(
    content: ft.Control,
    *,
    padding: int = SPACING['md'],
    width: int | float | None = None,
    expand: bool | int | None = None,
) -> ft.Container:
    kwargs: dict = dict(
        content=content,
        padding=padding,
        width=width,
        bgcolor=COLORS['surface_container'],
        border_radius=RADIUS_SURFACE,
        border=outline_border(),
    )
    if expand is not None:
        kwargs['expand'] = expand
    return ft.Container(**kwargs)


def CenteredCard(content: ft.Control, width: int = 380, padding: int = 40) -> ft.Card:
    return ft.Card(
        elevation=CARD_ELEVATION,
        content=ft.Container(
            content=content,
            padding=padding,
            width=width,
        ),
    )


def PageContainer(content: ft.Control, padding: int = 24) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        expand=True,
    )


def CenteredForm(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=CenteredCard(content, width=400, padding=SPACING['xl']),
        alignment=ft.alignment.center,
        expand=True,
    )


def StyledDropdown(label: str, options: list, width: int = 300) -> ft.Dropdown:
    dropdown_options = [ft.dropdown.Option(text=opt, key=opt) for opt in options]
    return ft.Dropdown(
        label=label,
        options=dropdown_options,
        width=width,
        filled=True,
        border_radius=RADIUS_FIELD,
    )
