import flet as ft
from api.client import APIClient, APIError
from authz import require_group_admin
from api.events import (
    get_event,
    list_event_songs,
    add_event_song,
    update_event_song,
    remove_event_song,
)
from api.songs import get_songs
from state.app_state import AppState
from components.styled import StyledDropdown, FormField, PrimaryButton, ErrorText, PageContainer, SurfaceCard, EmptyState, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, RADIUS_FIELD


def build_config_event_songs_page(page: ft.Page, state: AppState, slug: str, event_id: int) -> ft.View:
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)
    event_title = ft.Text('', size=FONT_SIZES['subtitle'], weight=ft.FontWeight.W_600)

    event_songs_list = ft.Column(spacing=SPACING['sm'], expand=True, scroll=ft.ScrollMode.AUTO)
    songs_dropdown = StyledDropdown('Música do grupo', [], width=None)
    order_field = FormField('Ordem', width=None)
    add_button = PrimaryButton('Adicionar à setlist', width=None)
    loading = ft.ProgressRing(visible=True)

    dropdown_key_to_song_id: dict[str, int] = {}

    async def load_context():
        if not await require_group_admin(page, state, slug):
            loading.visible = False
            page.update()
            return
        error_msg.visible = False
        loading.visible = True
        event_songs_list.controls.clear()
        page.update()

        client = APIClient(state, page)
        try:
            event = await get_event(client, slug, event_id)
            event_title.value = event.get('title', f'Evento {event_id}')

            group_songs = await get_songs(client, slug)
            dropdown_key_to_song_id.clear()
            options = []
            for song in group_songs:
                key = f"{song['title']} - {song.get('artist') or 'Sem artista'}"
                dropdown_key_to_song_id[key] = song['id']
                options.append(ft.dropdown.Option(text=key, key=key))
            songs_dropdown.options = options

            event_songs = await list_event_songs(client, slug, event_id)
            if not event_songs:
                event_songs_list.controls.append(
                    EmptyState('Nenhuma música associada ao evento.', icon=ft.icons.QUEUE_MUSIC_ROUNDED)
                )
            else:
                for event_song in event_songs:
                    event_songs_list.controls.append(_build_song_row(event_song))
        except APIError as ex:
            error_msg.value = ex.detail
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao carregar setlist do evento.'
            error_msg.visible = True
        finally:
            loading.visible = False
            page.update()

    def _build_song_row(event_song: dict) -> ft.Container:
        order_inline = ft.TextField(
            value=str(event_song.get('order', 0)),
            label='Ordem',
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
            filled=True,
            border_radius=RADIUS_FIELD,
        )

        async def on_save(_: ft.ControlEvent):
            error_msg.visible = False
            success_msg.visible = False
            try:
                new_order = int((order_inline.value or '0').strip())
            except ValueError:
                error_msg.value = 'Informe uma ordem numérica válida.'
                error_msg.visible = True
                page.update()
                return

            client = APIClient(state, page)
            try:
                await update_event_song(client, slug, event_id, event_song['id'], {'order': new_order})
                success_msg.value = 'Ordem da música atualizada.'
                success_msg.visible = True
                await load_context()
            except APIError as ex:
                error_msg.value = ex.detail
                error_msg.visible = True
                page.update()

        async def on_remove(_: ft.ControlEvent):
            error_msg.visible = False
            success_msg.visible = False
            client = APIClient(state, page)
            try:
                await remove_event_song(client, slug, event_id, event_song['id'])
                success_msg.value = 'Música removida da setlist.'
                success_msg.visible = True
                await load_context()
            except APIError as ex:
                error_msg.value = ex.detail
                error_msg.visible = True
                page.update()

        song = event_song.get('song', {})
        inner = ft.Column(
            [
                ft.Text(song.get('title', 'Sem título'), weight=ft.FontWeight.W_600),
                ft.Text(
                    f"{song.get('artist') or 'Sem artista'} • {song.get('key') or '-'}",
                    color=COLORS['secondary'],
                    size=FONT_SIZES['body'],
                ),
                ft.Row(
                    [
                        order_inline,
                        ft.TextButton('Salvar', on_click=on_save),
                        ft.TextButton('Remover', on_click=on_remove),
                    ],
                    spacing=SPACING['sm'],
                ),
            ],
            spacing=SPACING['sm'],
        )
        return SurfaceCard(inner, padding=SPACING['md'])

    async def handle_add(_: ft.ControlEvent):
        error_msg.visible = False
        success_msg.visible = False
        add_button.disabled = True
        page.update()

        selected_key = songs_dropdown.value
        song_id = dropdown_key_to_song_id.get(selected_key or '')
        if not song_id:
            error_msg.value = 'Selecione uma música do grupo.'
            error_msg.visible = True
            add_button.disabled = False
            page.update()
            return

        try:
            order = int((order_field.value or '0').strip())
        except ValueError:
            error_msg.value = 'Informe uma ordem numérica válida.'
            error_msg.visible = True
            add_button.disabled = False
            page.update()
            return

        client = APIClient(state, page)
        try:
            await add_event_song(client, slug, event_id, song_id=song_id, order=order)
            success_msg.value = 'Música adicionada à setlist.'
            success_msg.visible = True
            songs_dropdown.value = None
            order_field.value = ''
            await load_context()
        except APIError as ex:
            error_msg.value = ex.detail
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao adicionar música na setlist.'
            error_msg.visible = True
        finally:
            add_button.disabled = False
            page.update()

    def go_back(_: ft.ControlEvent):
        page.go(f'/groups/{slug}/events')

    add_button.on_click = handle_add
    page.run_task(load_context)

    add_panel = SurfaceCard(
        ft.Column(
            [
                ft.Text('Adicionar música ao evento', weight=ft.FontWeight.W_600),
                songs_dropdown,
                order_field,
                add_button,
            ],
            spacing=SPACING['md'],
        ),
        padding=SPACING['md'],
    )

    content = ft.Column(
        [
            event_title,
            error_msg,
            success_msg,
            SectionTitle('Setlist do evento'),
            loading,
            SurfaceCard(event_songs_list, padding=SPACING['sm'], expand=1),
            SectionTitle('Adicionar música'),
            add_panel,
        ],
        spacing=SPACING['md'],
        expand=True,
    )

    return ft.View(
        f'/groups/{slug}/events/{event_id}/songs',
        [
            ft.AppBar(
                title=ft.Text('Setlist do evento'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
