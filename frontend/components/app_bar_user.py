import flet as ft

from state.app_state import AppState
from theme import COLORS, FONT_SIZES, SPACING


def _display_name(user: dict | None) -> str:
    if not user:
        return ''
    fn = (user.get('first_name') or '').strip()
    ln = (user.get('last_name') or '').strip()
    parts = [p for p in (fn, ln) if p]
    if parts:
        return ' '.join(parts)
    return (user.get('username') or '').strip() or 'Usuário'


def _initials(user: dict | None) -> str:
    if not user:
        return '?'
    fn = (user.get('first_name') or '').strip()
    ln = (user.get('last_name') or '').strip()
    if fn and ln:
        return (fn[0] + ln[0]).upper()
    if fn:
        return fn[0].upper()
    u = (user.get('username') or '?').strip()
    return (u[:2] if len(u) >= 2 else u).upper()


def app_bar_user_row(page: ft.Page, state: AppState) -> ft.Control:
    """Avatar + nome do usuário logado para `AppBar.actions` (clique abre o perfil)."""
    u = state.user
    name = _display_name(u)
    photo = ((u or {}).get('photo') or '').strip() or None

    if photo:
        avatar = ft.CircleAvatar(radius=18, foreground_image_url=photo)
    else:
        avatar = ft.CircleAvatar(
            radius=18,
            bgcolor=COLORS['surface_container'],
            color=COLORS['primary'],
            content=ft.Text(_initials(u), size=12, weight=ft.FontWeight.W_600),
        )

    label = ft.Container(
        content=ft.Text(
            name,
            size=FONT_SIZES['label'],
            weight=ft.FontWeight.W_500,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
        width=180,
    )
    inner = ft.Row(
        [avatar, label],
        spacing=SPACING['sm'],
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    wrapped = ft.Container(
        content=inner,
        padding=ft.padding.only(left=SPACING['sm'], right=SPACING['sm']),
    )

    def go_profile(_: object | None = None) -> None:
        if page.route != '/profile':
            page.go('/profile')

    return ft.Tooltip(
        message='Meu perfil',
        content=ft.GestureDetector(
            content=wrapped,
            on_tap=go_profile,
            mouse_cursor=ft.MouseCursor.CLICK,
        ),
    )
