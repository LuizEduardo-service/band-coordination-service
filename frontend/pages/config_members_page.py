import flet as ft
import asyncio
from api.client import APIClient, APIError
from api.groups import add_member, remove_member
from api.invites import create_group_invite
from authz import require_group_admin
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, StyledDropdown, PageContainer, SurfaceCard, EmptyState, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING
from instrument_icons import format_instruments_slugs


def build_config_members_page(page: ft.Page, state: AppState, slug: str) -> ft.View:
    search_field = FormField(label='Buscar usuário', width=None)
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)

    search_results = ft.Column(spacing=SPACING['sm'], expand=True, scroll=ft.ScrollMode.AUTO)
    members_list = ft.Column(spacing=SPACING['sm'], expand=True, scroll=ft.ScrollMode.AUTO)

    role_dropdown = StyledDropdown('Tipo de membro', ['admin', 'member'])

    search_task = None

    async def handle_search_debounced(query: str):
        if not query:
            search_results.controls.clear()
            page.update()
            return

        client = APIClient(state, page)
        try:
            users = await client.get(f'/users/?search={query}')
            search_results.controls.clear()

            if not users:
                search_results.controls.append(
                    EmptyState('Nenhum usuário encontrado.', icon=ft.icons.PERSON_SEARCH_OUTLINED)
                )
            else:
                for user in users:
                    def make_add_click(user_id, user_name):
                        async def add_click(e):
                            if not role_dropdown.value:
                                error_msg.value = 'Selecione o tipo de membro.'
                                error_msg.visible = True
                                page.update()
                                return

                            client2 = APIClient(state, page)
                            try:
                                await add_member(client2, slug, user_id, role_dropdown.value)
                                success_msg.value = f'{user_name} adicionado!'
                                success_msg.visible = True
                                search_field.value = ''
                                search_results.controls.clear()
                                page.update()
                                await load_members()
                            except APIError as ex:
                                error_msg.value = ex.message
                                error_msg.visible = True
                                page.update()
                        return add_click

                    def make_invite_click(user_id, user_name):
                        async def invite_click(e):
                            if not role_dropdown.value:
                                error_msg.value = 'Selecione o tipo de membro para o convite.'
                                error_msg.visible = True
                                page.update()
                                return
                            client2 = APIClient(state, page)
                            try:
                                await create_group_invite(client2, slug, user_id, role_dropdown.value)
                                success_msg.value = f'Convite enviado para {user_name}.'
                                success_msg.visible = True
                                search_field.value = ''
                                search_results.controls.clear()
                                page.update()
                            except APIError as ex:
                                error_msg.value = ex.message
                                error_msg.visible = True
                                page.update()
                        return invite_click

                    add_btn = PrimaryButton('Adicionar', width=100)
                    add_btn.on_click = make_add_click(user['id'], user['username'])
                    invite_btn = ft.OutlinedButton('Convidar', width=100, on_click=make_invite_click(user['id'], user['username']))
                    row_inner = ft.Column(
                        [
                            ft.Column(
                                [
                                    ft.Text(user['username'], weight=ft.FontWeight.W_500),
                                    ft.Text(user.get('email', ''), size=FONT_SIZES['body'], color=COLORS['secondary']),
                                    ft.Text(
                                        f"Instrumentos no perfil: {format_instruments_slugs(user.get('instruments'))}",
                                        size=FONT_SIZES['body'],
                                        color=COLORS['secondary'],
                                    ),
                                ],
                                spacing=SPACING['xs'],
                            ),
                            ft.Row([add_btn, invite_btn], spacing=SPACING['sm'], wrap=True),
                        ],
                        spacing=SPACING['sm'],
                    )
                    search_results.controls.append(SurfaceCard(row_inner, padding=SPACING['sm']))
        except Exception as ex:
            error_msg.value = 'Erro ao buscar usuários.'
            error_msg.visible = True
        page.update()

    async def handle_search(e):
        nonlocal search_task

        query = search_field.value.strip()

        if search_task:
            search_task.cancel()

        async def debounced_search():
            await asyncio.sleep(0.5)
            await handle_search_debounced(query)

        search_task = asyncio.create_task(debounced_search())

    async def load_members():
        if not await require_group_admin(page, state, slug):
            return
        client = APIClient(state, page)
        try:
            from api.groups import get_members
            members = await get_members(client, slug)
            members_list.controls.clear()

            if not members:
                members_list.controls.append(
                    EmptyState('Nenhum membro no grupo.', icon=ft.icons.PEOPLE_OUTLINE)
                )
            else:
                for member in members:
                    def make_remove_click(member_id):
                        async def remove_click(e):
                            client2 = APIClient(state, page)
                            try:
                                await remove_member(client2, slug, member_id)
                                success_msg.value = 'Membro removido!'
                                success_msg.visible = True
                                page.update()
                                await load_members()
                            except APIError as ex:
                                error_msg.value = ex.message
                                error_msg.visible = True
                                page.update()
                        return remove_click

                    row_inner = ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(member['user']['username'], weight=ft.FontWeight.W_500),
                                    ft.Text(member['role'].upper(), size=FONT_SIZES['body'], color=COLORS['secondary']),
                                    ft.Text(
                                        format_instruments_slugs(member['user'].get('instruments')),
                                        size=FONT_SIZES['body'],
                                        color=COLORS['secondary'],
                                    ),
                                ],
                                expand=True,
                            ),
                            ft.IconButton(
                                ft.icons.DELETE_OUTLINE,
                                on_click=make_remove_click(member['id']),
                                tooltip='Remover',
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                    members_list.controls.append(SurfaceCard(row_inner, padding=SPACING['sm']))
        except APIError as ex:
            error_msg.value = f"Erro ao carregar membros: {ex.message}"
            error_msg.visible = True
        page.update()

    search_field.on_change = handle_search
    page.run_task(load_members)

    content = ft.Column(
        [
            error_msg,
            success_msg,
            SectionTitle('Membros atuais'),
            SurfaceCard(members_list, padding=SPACING['sm'], expand=1),
            SectionTitle('Adicionar membro'),
            SurfaceCard(
                ft.Column(
                    [
                        search_field,
                        ft.Text('Resultados', size=FONT_SIZES['label'], weight=ft.FontWeight.W_500),
                        SurfaceCard(search_results, padding=SPACING['sm']),
                        ft.Text('Tipo de membro', size=FONT_SIZES['label'], weight=ft.FontWeight.W_500),
                        role_dropdown,
                        ft.Text(
                            'Os instrumentos são definidos no perfil de cada usuário (Meu perfil).',
                            size=FONT_SIZES['body'],
                            color=COLORS['secondary'],
                        ),
                    ],
                    spacing=SPACING['md'],
                ),
                padding=SPACING['md'],
            ),
        ],
        expand=True,
        spacing=SPACING['md'],
    )

    def go_back(_):
        page.go(f'/groups/{slug}')

    return ft.View(
        f'/groups/{slug}/members',
        [
            ft.AppBar(
                title=ft.Text('Gerenciar membros'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
