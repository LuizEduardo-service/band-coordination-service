import flet as ft
from api.client import APIClient, APIError
from api.groups import list_groups
from api.invites import pending_invite_count
from api.song_suggestions import pending_song_suggestion_count
from state.app_state import AppState
from components.styled import PageContainer, ErrorText, EmptyState, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, CARD_ELEVATION, RADIUS_CARD


def build_dashboard_page(page: ft.Page, state: AppState) -> ft.View:
    groups_list = ft.Column(spacing=SPACING['md'], expand=True)
    loading = ft.ProgressRing(visible=True)
    error_msg = ErrorText()

    user_name = state.user.get('first_name') or state.user.get('username', '') if state.user else ''

    invite_mail_btn = ft.IconButton(icon=ft.icons.MAIL_OUTLINE, tooltip='Notificações')
    invite_badge = ft.Badge(content=invite_mail_btn, text='', label_visible=False, bgcolor=COLORS['error'])

    async def refresh_invite_badge():
        client = APIClient(state, page)
        try:
            n_inv = await pending_invite_count(client)
            n_sug = await pending_song_suggestion_count(client)
            n = n_inv + n_sug
            invite_badge.text = str(n) if n > 0 else ''
            invite_badge.label_visible = n > 0
        except Exception:
            pass
        page.update()

    def open_invites(_: ft.ControlEvent) -> None:
        page.go('/invites')

    invite_mail_btn.on_click = open_invites

    async def load_groups():
        client = APIClient(state, page)
        try:
            groups = await list_groups(client)
            loading.visible = False
            if not groups:
                groups_list.controls.append(
                    EmptyState('Nenhum grupo encontrado. Crie um pelo menu.', icon=ft.icons.GROUPS_OUTLINED)
                )
            else:
                for group in groups:
                    groups_list.controls.append(_group_card(group))
            await refresh_invite_badge()
        except APIError as ex:
            loading.visible = False
            error_msg.value = ex.detail
            error_msg.visible = True
        page.update()

    def _group_card(group: dict) -> ft.Card:
        def on_tap(_):
            state.current_group = group
            page.go(f'/groups/{group["slug"]}')

        return ft.Card(
            elevation=CARD_ELEVATION,
            content=ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.icons.MUSIC_NOTE_ROUNDED, color=COLORS['primary']),
                    title=ft.Text(group['name'], weight=ft.FontWeight.W_600),
                    subtitle=ft.Text(
                        group.get('description', '') or 'Toque para abrir',
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        color=COLORS['secondary'],
                    ),
                    on_click=on_tap,
                ),
                padding=SPACING['xs'],
                border_radius=RADIUS_CARD,
            ),
        )

    async def handle_logout(_):
        state.clear(page)
        page.go('/login')

    page.run_task(load_groups)

    header_row = (
        ft.Column(
            [
                ft.Text(
                    f'Olá, {user_name}',
                    size=FONT_SIZES['subtitle'],
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    'Escolha um grupo para ver a escala',
                    size=FONT_SIZES['body'],
                    color=COLORS['secondary'],
                ),
            ],
            spacing=SPACING['xs'],
            tight=True,
        )
        if user_name
        else ft.Text(
            'Meus grupos',
            size=FONT_SIZES['subtitle'],
            weight=ft.FontWeight.W_600,
        )
    )

    content = ft.Column(
        [
            header_row,
            SectionTitle('Grupos'),
            loading,
            error_msg,
            groups_list,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=SPACING['md'],
    )

    def open_drawer(_: ft.ControlEvent) -> None:
        drawer.open = True
        page.update()

    def close_drawer() -> None:
        drawer.open = False
        page.update()

    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text('Escala Louvor', size=FONT_SIZES['subtitle'], weight=ft.FontWeight.W_600),
                        ft.Text('Navegação', size=FONT_SIZES['body'], color=COLORS['secondary']),
                    ],
                    spacing=SPACING['xs'],
                    tight=True,
                ),
                padding=SPACING['md'],
            ),
            ft.Divider(height=1),
            ft.NavigationDrawerDestination(
                label='Meus Grupos',
                icon=ft.icons.GROUPS_OUTLINED,
                selected_icon=ft.icons.GROUPS,
            ),
            ft.NavigationDrawerDestination(
                label='Notificações',
                icon=ft.icons.MAIL_OUTLINE,
                selected_icon=ft.icons.MAIL,
            ),
            ft.NavigationDrawerDestination(
                label='Meu perfil',
                icon=ft.icons.PERSON_OUTLINED,
                selected_icon=ft.icons.PERSON,
            ),
            ft.NavigationDrawerDestination(
                label='Criar Novo Grupo',
                icon=ft.icons.ADD_CIRCLE_OUTLINE,
                selected_icon=ft.icons.ADD_CIRCLE,
            ),
            ft.NavigationDrawerDestination(
                label='Configurar Grupo',
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
            ),
            ft.Divider(height=1),
            ft.NavigationDrawerDestination(
                label='Sair',
                icon=ft.icons.LOGOUT,
                selected_icon=ft.icons.LOGOUT,
            ),
        ],
    )

    def on_drawer_change(e):
        if drawer.selected_index == 0:
            close_drawer()
        elif drawer.selected_index == 1:
            close_drawer()
            page.go('/invites')
        elif drawer.selected_index == 2:
            close_drawer()
            page.go('/profile')
        elif drawer.selected_index == 3:
            close_drawer()
            page.go('/config/groups/create')
        elif drawer.selected_index == 4:
            close_drawer()
            page.go('/config/groups/settings')
        elif drawer.selected_index == 5:
            close_drawer()
            handle_logout(None)

    drawer.on_change = on_drawer_change

    return ft.View(
        '/dashboard',
        [
            ft.AppBar(
                title=ft.Text('Escala Louvor'),
                center_title=False,
                leading=ft.IconButton(ft.icons.MENU_ROUNDED, on_click=open_drawer, tooltip='Menu'),
                actions=[
                    invite_badge,
                    app_bar_user_row(page, state),
                    ft.TextButton('Sair', on_click=handle_logout),
                ],
            ),
            PageContainer(content),
        ],
        drawer=drawer,
    )
