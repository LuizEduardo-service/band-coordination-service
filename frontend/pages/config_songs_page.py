import math
import flet as ft
from api.client import APIClient, APIError
from api.songs import get_songs, delete_song
from authz import require_group_admin
from state.app_state import AppState
from components.styled import (
    ErrorText, PageContainer, SurfaceCard, EmptyState, SectionTitle
)
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING

PAGE_SIZE = 10


def build_config_songs_page(page: ft.Page, state: AppState, slug: str) -> ft.View:
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)

    songs_list = ft.Column(spacing=SPACING['sm'], expand=True, scroll=ft.ScrollMode.AUTO)
    all_songs: list = []
    filtered_songs: list = []
    page_num = [0]

    search_field = ft.TextField(
        hint_text='Pesquisar músicas...',
        prefix_icon=ft.icons.SEARCH_ROUNDED,
        filled=True,
        border_radius=8,
        expand=True,
        dense=True,
    )
    cb_title = ft.Checkbox(label='Título', value=True)
    cb_artist = ft.Checkbox(label='Artista', value=False)

    btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT_ROUNDED, disabled=True)
    btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT_ROUNDED, disabled=True)
    page_label = ft.Text('Página 1 de 1', color=COLORS['secondary'], size=FONT_SIZES['body'])

    # --- Detail bottom sheet ---
    sheet_body = ft.Column(spacing=SPACING['md'], tight=True)
    detail_sheet = ft.BottomSheet(
        content=ft.Container(content=sheet_body, padding=SPACING['lg']),
        open=False,
    )
    page.overlay.append(detail_sheet)

    def open_detail(song: dict):
        sheet_body.controls.clear()
        key_text = song.get('key_display') or song.get('key', '')

        sheet_body.controls.append(
            ft.Text(song['title'], size=FONT_SIZES['subtitle'], weight=ft.FontWeight.W_600)
        )
        sheet_body.controls.append(
            ft.Text(song['artist'], color=COLORS['secondary'])
        )
        sheet_body.controls.append(ft.Divider())
        sheet_body.controls.append(
            ft.Row(
                [ft.Text('Tom:', weight=ft.FontWeight.W_500), ft.Text(key_text)],
                spacing=SPACING['sm'],
            )
        )
        if song.get('notes'):
            sheet_body.controls.append(ft.Text('Notas:', weight=ft.FontWeight.W_500))
            sheet_body.controls.append(ft.Text(song['notes'], color=COLORS['secondary']))
        if song.get('link'):
            sheet_body.controls.append(
                ft.TextButton(
                    'Abrir link de referência',
                    icon=ft.icons.OPEN_IN_NEW_ROUNDED,
                    on_click=lambda _, lnk=song['link']: page.launch_url(lnk),
                )
            )
        detail_sheet.open = True
        page.update()

    # --- Render ---
    def render_page():
        start = page_num[0] * PAGE_SIZE
        songs_slice = filtered_songs[start:start + PAGE_SIZE]

        songs_list.controls.clear()
        if not filtered_songs:
            songs_list.controls.append(
                EmptyState('Nenhuma música encontrada.', icon=ft.icons.QUEUE_MUSIC_ROUNDED)
            )
        else:
            for song in songs_slice:
                def make_remove_click(song_id):
                    async def remove_click(e):
                        client2 = APIClient(state, page)
                        try:
                            await delete_song(client2, slug, song_id)
                            success_msg.value = 'Música removida!'
                            success_msg.visible = True
                            page.update()
                            await load_songs()
                        except APIError as ex:
                            error_msg.value = ex.message
                            error_msg.visible = True
                            page.update()
                    return remove_click

                def make_detail_click(s):
                    return lambda _: open_detail(s)

                row_inner = ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(song['title'], weight=ft.FontWeight.W_500),
                                ft.Text(
                                    f"{song['artist']} • {song.get('key_display') or song['key']}",
                                    size=FONT_SIZES['body'],
                                    color=COLORS['secondary'],
                                ),
                            ],
                            expand=True,
                        ),
                        ft.IconButton(
                            ft.icons.DELETE_OUTLINE,
                            on_click=make_remove_click(song['id']),
                            tooltip='Remover',
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
                card = SurfaceCard(row_inner, padding=SPACING['sm'])
                card.on_click = make_detail_click(song)
                card.ink = True
                songs_list.controls.append(card)

        total_pages = max(1, math.ceil(len(filtered_songs) / PAGE_SIZE))
        page_label.value = f'Página {page_num[0] + 1} de {total_pages}'
        btn_prev.disabled = page_num[0] == 0
        btn_next.disabled = page_num[0] >= total_pages - 1
        page.update()

    def apply_filter(_=None):
        query = search_field.value.strip().lower()
        filtered_songs.clear()
        if not query:
            filtered_songs.extend(all_songs)
        else:
            filtered_songs.extend(
                s for s in all_songs
                if (cb_title.value and query in s['title'].lower())
                or (cb_artist.value and query in s['artist'].lower())
            )
        page_num[0] = 0
        render_page()

    def go_prev(_):
        page_num[0] -= 1
        render_page()

    def go_next(_):
        page_num[0] += 1
        render_page()

    btn_prev.on_click = go_prev
    btn_next.on_click = go_next
    search_field.on_change = apply_filter
    cb_title.on_change = apply_filter
    cb_artist.on_change = apply_filter

    async def load_songs():
        if not await require_group_admin(page, state, slug):
            return
        client = APIClient(state, page)
        try:
            songs = await get_songs(client, slug)
            all_songs.clear()
            all_songs.extend(songs)
            apply_filter()
        except APIError as ex:
            error_msg.value = f'Erro ao carregar músicas: {ex.message}'
            error_msg.visible = True
            page.update()

    page.run_task(load_songs)

    search_block = SurfaceCard(
        ft.Column(
            [
                ft.Row([search_field]),
                ft.Row([cb_title, cb_artist], spacing=SPACING['md']),
            ],
            spacing=SPACING['sm'],
        ),
        padding=SPACING['sm'],
    )

    pagination_row = ft.Row(
        [btn_prev, page_label, btn_next],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    add_btn = ft.FilledTonalButton(
        '+ Nova música',
        on_click=lambda _: page.go(f'/groups/{slug}/songs/new'),
    )

    content = ft.Column(
        [
            error_msg,
            success_msg,
            SectionTitle('Repertório', trailing=add_btn),
            search_block,
            SurfaceCard(songs_list, padding=SPACING['sm'], expand=1),
            pagination_row,
        ],
        expand=True,
        spacing=SPACING['md'],
    )

    def go_back(_):
        page.go(f'/groups/{slug}')

    return ft.View(
        f'/groups/{slug}/songs',
        [
            ft.AppBar(
                title=ft.Text('Gerenciar músicas'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
