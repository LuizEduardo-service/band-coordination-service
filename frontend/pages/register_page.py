import flet as ft
from api.client import APIClient, APIError
from api.auth import register_account, login, get_me
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, Spacer, CenteredForm
from theme import COLORS, FONT_SIZES, SPACING


def build_register_page(page: ft.Page, state: AppState) -> ft.View:
    username = FormField(label='Usuário', autofocus=True)
    email = FormField(label='E-mail')
    first_name = FormField(label='Nome')
    last_name = FormField(label='Sobrenome')
    password = FormField(label='Senha', password=True)
    password2 = FormField(label='Confirmar senha', password=True)
    error_msg = ErrorText()
    btn = PrimaryButton('Criar conta')

    async def handle_register(_):
        error_msg.visible = False
        btn.disabled = True
        page.update()

        client = APIClient(state, page)
        try:
            await register_account(
                client,
                {
                    'username': username.value.strip(),
                    'email': email.value.strip(),
                    'first_name': first_name.value.strip(),
                    'last_name': last_name.value.strip(),
                    'password': password.value,
                    'password2': password2.value,
                },
            )
            data = await login(client, username.value.strip(), password.value)
            state.token = data['access']
            state.refresh_token = data['refresh']
            me = await get_me(client)
            state.user = me
            state.save(page)
            page.go('/dashboard')
        except APIError as ex:
            d = ex.detail
            error_msg.value = d if isinstance(d, str) else str(d)
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro de conexão. Verifique se o servidor está rodando.'
            error_msg.visible = True
        finally:
            btn.disabled = False
            page.update()

    def go_login(_):
        page.go('/login')

    btn.on_click = handle_register

    form_content = ft.Column(
        [
            ft.Icon(ft.icons.PERSON_ADD_ROUNDED, size=48, color=COLORS['primary']),
            ft.Text(
                'Criar conta',
                size=FONT_SIZES['title'],
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                'Cadastre-se para receber convites e participar das escalas',
                size=FONT_SIZES['label'],
                color=COLORS['secondary'],
                text_align=ft.TextAlign.CENTER,
            ),
            Spacer(),
            username,
            email,
            first_name,
            last_name,
            password,
            password2,
            error_msg,
            Spacer(height=SPACING['sm']),
            btn,
            ft.TextButton('Já tenho conta', on_click=go_login),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=SPACING['md'],
        tight=True,
    )

    return ft.View(
        '/register',
        [CenteredForm(form_content)],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=COLORS['background'],
    )
