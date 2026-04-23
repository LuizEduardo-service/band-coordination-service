import flet as ft
from api.client import APIClient, APIError
from api.auth import login, get_me
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, Spacer, CenteredForm
from theme import COLORS, FONT_SIZES, SPACING, ICON_SIZES


def build_login_page(page: ft.Page, state: AppState) -> ft.View:
    username = FormField(label='Usuário', autofocus=True)
    password = FormField(label='Senha', password=True)
    error_msg = ErrorText()
    btn = PrimaryButton('Entrar')

    async def handle_login(e):
        error_msg.visible = False
        btn.disabled = True
        page.update()

        client = APIClient(state, page)
        try:
            data = await login(client, username.value.strip(), password.value)
            state.token = data['access']
            state.refresh_token = data['refresh']

            me = await get_me(client)
            state.user = me
            state.save(page)

            page.go('/dashboard')
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
        except Exception as ex:
            error_msg.value = 'Erro de conexão. Verifique se o servidor está rodando.'
            error_msg.visible = True
        finally:
            btn.disabled = False
            page.update()

    btn.on_click = handle_login
    password.on_submit = handle_login

    form_content = ft.Column(
        [
            ft.Icon(ft.icons.CHURCH_ROUNDED, size=ICON_SIZES['hero'], color=COLORS['primary']),
            ft.Text(
                'Escala Louvor',
                size=FONT_SIZES['title'],
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                'Acesse sua conta para continuar',
                size=FONT_SIZES['label'],
                color=COLORS['secondary'],
                text_align=ft.TextAlign.CENTER,
            ),
            Spacer(),
            username,
            password,
            error_msg,
            Spacer(height=SPACING['sm']),
            btn,
            ft.TextButton('Criar conta', on_click=lambda _: page.go('/register')),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=SPACING['md'],
        tight=True,
    )

    return ft.View(
        '/login',
        [CenteredForm(form_content)],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=COLORS['background'],
    )
