import flet as ft
from api.client import APIClient, APIError
from api.groups import create_group
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, Spacer, CenteredForm
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING


def build_config_group_page(page: ft.Page, state: AppState) -> ft.View:
    name_field = FormField(label='Nome do Grupo')
    description_field = FormField(label='Descrição (opcional)')
    error_msg = ErrorText()
    btn = PrimaryButton('Criar grupo')

    async def handle_create(e):
        error_msg.visible = False
        btn.disabled = True
        page.update()

        if not name_field.value.strip():
            error_msg.value = 'Nome do grupo é obrigatório.'
            error_msg.visible = True
            btn.disabled = False
            page.update()
            return

        client = APIClient(state, page)
        try:
            data = await create_group(client, name_field.value.strip(), description_field.value.strip())
            page.go('/dashboard')
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao criar grupo.'
            error_msg.visible = True
        finally:
            btn.disabled = False
            page.update()

    btn.on_click = handle_create

    form_content = ft.Column(
        [
            ft.Icon(ft.icons.GROUP_ADD_ROUNDED, size=40, color=COLORS['primary']),
            ft.Text('Criar novo grupo', size=FONT_SIZES['title'], weight=ft.FontWeight.W_600),
            ft.Text(
                'Defina nome e descrição para o ministério',
                size=FONT_SIZES['body'],
                color=COLORS['secondary'],
                text_align=ft.TextAlign.CENTER,
            ),
            Spacer(),
            name_field,
            description_field,
            error_msg,
            Spacer(height=SPACING['sm']),
            btn,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=SPACING['md'],
        tight=True,
    )

    def go_back(_):
        page.go('/dashboard')

    return ft.View(
        '/config/groups/create',
        [
            ft.AppBar(
                title=ft.Text('Criar grupo'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            CenteredForm(form_content),
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=COLORS['background'],
    )
