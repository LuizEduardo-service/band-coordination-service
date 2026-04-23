import flet as ft
from api.client import APIClient, APIError
from api.songs import add_song
from authz import require_group_admin
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, StyledDropdown, PageContainer, SurfaceCard
from components.app_bar_user import app_bar_user_row
from theme import COLORS, SPACING
from constants import TONALITIES


def build_add_song_page(page: ft.Page, state: AppState, slug: str) -> ft.View:
    title_field = FormField(label='Título da música', autofocus=True)
    artist_field = FormField(label='Artista')
    key_dropdown = StyledDropdown('Tonalidade', TONALITIES)
    notes_field = FormField(label='Notas (opcional)')
    link_field = FormField(label='Link de referência (opcional)')
    error_msg = ErrorText()
    btn = PrimaryButton('Adicionar música')

    async def handle_add_song(e):
        error_msg.visible = False
        btn.disabled = True
        page.update()

        if not title_field.value.strip():
            error_msg.value = 'Título é obrigatório.'
            error_msg.visible = True
            btn.disabled = False
            page.update()
            return

        if not artist_field.value.strip():
            error_msg.value = 'Artista é obrigatório.'
            error_msg.visible = True
            btn.disabled = False
            page.update()
            return

        if not key_dropdown.value:
            error_msg.value = 'Tonalidade é obrigatória.'
            error_msg.visible = True
            btn.disabled = False
            page.update()
            return

        client = APIClient(state, page)
        try:
            await add_song(
                client, slug,
                title_field.value.strip(),
                artist_field.value.strip(),
                key_dropdown.value,
                notes_field.value.strip(),
                link_field.value.strip(),
            )
            page.go(f'/groups/{slug}/songs')
        except APIError as ex:
            error_msg.value = ex.detail
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao adicionar música.'
            error_msg.visible = True
        finally:
            btn.disabled = False
            page.update()

    async def check_access():
        await require_group_admin(page, state, slug)

    btn.on_click = handle_add_song
    page.run_task(check_access)

    form_block = SurfaceCard(
        ft.Column(
            [
                error_msg,
                title_field,
                artist_field,
                key_dropdown,
                notes_field,
                link_field,
                btn,
            ],
            spacing=SPACING['md'],
        ),
        padding=SPACING['md'],
    )

    def go_back(_):
        page.go(f'/groups/{slug}/songs')

    return ft.View(
        f'/groups/{slug}/songs/new',
        [
            ft.AppBar(
                title=ft.Text('Nova música'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(form_block),
        ],
    )
