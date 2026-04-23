import asyncio
import flet as ft
from api.client import APIClient, APIError
from api.song_suggestions import create_song_suggestion
from state.app_state import AppState
from components.styled import PageContainer, ErrorText, EmptyState, SectionTitle, PrimaryButton, FormField
from constants import TONALITIES
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, CARD_ELEVATION, RADIUS_CARD, RADIUS_FIELD, outline_border
from instrument_icons import format_instruments_slugs
from utils.date_utils import format_event_date


def build_group_page(page: ft.Page, state: AppState, slug: str) -> ft.View:
    group_title = ft.Text('', size=FONT_SIZES['subtitle'], weight=ft.FontWeight.W_600)
    error_msg = ErrorText()
    user_is_group_admin = False

    members_content = ft.ListView(
        expand=True,
        spacing=SPACING['sm'],
        padding=ft.padding.only(bottom=SPACING['md']),
    )
    songs_content = ft.ListView(
        expand=True,
        spacing=SPACING['sm'],
        padding=ft.padding.only(bottom=SPACING['md']),
    )
    events_list = ft.ListView(
        expand=True,
        spacing=SPACING['sm'],
        padding=ft.padding.only(bottom=SPACING['md']),
    )

    loading_members = ft.ProgressRing(visible=True)
    loading_songs = ft.ProgressRing(visible=True)
    loading_events = ft.ProgressRing(visible=True)
    events_filter = ft.Dropdown(
        label='Filtro',
        value='all',
        filled=True,
        dense=True,
        border_radius=RADIUS_FIELD,
        options=[
            ft.dropdown.Option(key='all', text='Todos'),
            ft.dropdown.Option(key='upcoming', text='Próximos'),
            ft.dropdown.Option(key='past', text='Passados'),
        ],
    )
    events_filter_container = ft.Container(content=events_filter, width=130)

    events_data: list[dict] = []

    async def load_group():
        nonlocal user_is_group_admin
        client = APIClient(state, page)
        try:
            group = await client.get(f'/groups/{slug}/')
            group_title.value = group.get('name', slug)
            user_is_group_admin = group.get('my_role') == 'admin'
            manage_events_btn.visible = user_is_group_admin
            btn_add_member.visible = user_is_group_admin
            btn_add_song.visible = user_is_group_admin
            btn_suggest_song.visible = not user_is_group_admin
            render_events_list()
        except APIError as ex:
            error_msg.value = f"Erro ao carregar grupo: {ex.message}"
            error_msg.visible = True
            group_title.value = slug
        page.update()

    async def load_members():
        client = APIClient(state, page)
        try:
            from api.groups import get_members
            members = await get_members(client, slug)
            loading_members.visible = False
            members_content.controls.clear()
            if not members:
                members_content.controls.append(
                    EmptyState('Nenhum membro encontrado.', icon=ft.icons.PEOPLE_OUTLINE)
                )
            else:
                for member in members:
                    members_content.controls.append(
                        ft.Card(
                            elevation=CARD_ELEVATION,
                            content=ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.icons.PERSON_OUTLINE, color=COLORS['primary']),
                                    title=ft.Text(member['user']['username'], weight=ft.FontWeight.W_600),
                                    subtitle=ft.Text(
                                        f"{member['role'].upper()} • "
                                        f"{format_instruments_slugs(member['user'].get('instruments'))}",
                                        color=COLORS['secondary'],
                                    ),
                                ),
                                padding=ft.padding.symmetric(horizontal=SPACING['xs']),
                                border_radius=RADIUS_CARD,
                            ),
                        )
                    )
        except APIError as ex:
            loading_members.visible = False
            error_msg.value = f"Erro ao carregar membros: {ex.message}"
            error_msg.visible = True
        page.update()

    async def load_songs():
        client = APIClient(state, page)
        try:
            from api.songs import get_songs
            songs = await get_songs(client, slug)
            loading_songs.visible = False
            songs_content.controls.clear()
            if not songs:
                songs_content.controls.append(
                    EmptyState('Nenhuma música encontrada.', icon=ft.icons.QUEUE_MUSIC_ROUNDED)
                )
            else:
                for song in songs:
                    songs_content.controls.append(
                        ft.Card(
                            elevation=CARD_ELEVATION,
                            content=ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.icons.MUSIC_NOTE_ROUNDED, color=COLORS['primary']),
                                    title=ft.Text(song['title'], weight=ft.FontWeight.W_600),
                                    subtitle=ft.Text(
                                        f"{song['artist']} • {song['key']}",
                                        color=COLORS['secondary'],
                                    ),
                                ),
                                padding=ft.padding.symmetric(horizontal=SPACING['xs']),
                                border_radius=RADIUS_CARD,
                            ),
                        )
                    )
        except APIError as ex:
            loading_songs.visible = False
            error_msg.value = f"Erro ao carregar músicas: {ex.message}"
            error_msg.visible = True
        page.update()

    async def load_events():
        nonlocal events_data
        client = APIClient(state, page)
        try:
            from api.events import list_events
            filter_value = events_filter.value or 'all'
            upcoming = None
            ordering = '-date'
            if filter_value == 'upcoming':
                upcoming = True
                ordering = 'date'
            elif filter_value == 'past':
                upcoming = False
                ordering = '-date'

            events = await list_events(client, slug, upcoming=upcoming, ordering=ordering)
            loading_events.visible = False
            events_data = events
            render_events_list()
        except APIError as ex:
            loading_events.visible = False
            error_msg.value = f"Erro ao carregar eventos: {ex.message}"
            error_msg.visible = True
        except Exception:
            loading_events.visible = False
            error_msg.value = 'Erro ao carregar eventos.'
            error_msg.visible = True
        page.update()

    def go_to_events(_):
        page.go(f'/groups/{slug}/events')

    def _build_event_object_card(event: dict) -> ft.Card:
        event_id = event.get('id')

        def open_event_detail(_: ft.ControlEvent):
            page.go(f'/groups/{slug}/events/{event_id}')

        def open_event_members(_: ft.ControlEvent):
            page.go(f'/groups/{slug}/events/{event_id}/members')

        def open_event_songs(_: ft.ControlEvent):
            page.go(f'/groups/{slug}/events/{event_id}/songs')

        meta = (
            f"{format_event_date(event.get('date', ''))}  ·  "
            f"Membros: {event.get('member_count', 0)}  ·  "
            f"Músicas: {event.get('song_count', 0)}"
        )

        actions_row = ft.Row(
            [
                ft.IconButton(
                    icon=ft.icons.EVENT_ROUNDED,
                    tooltip='Detalhes',
                    on_click=open_event_detail,
                ),
                ft.IconButton(
                    icon=ft.icons.GROUP_OUTLINED,
                    tooltip='Membros',
                    on_click=open_event_members,
                    visible=user_is_group_admin,
                ),
                ft.IconButton(
                    icon=ft.icons.QUEUE_MUSIC_ROUNDED,
                    tooltip='Setlist',
                    on_click=open_event_songs,
                    visible=user_is_group_admin,
                ),
            ],
            spacing=0,
            tight=True,
        )

        inner = ft.Row(
            [
                ft.Icon(ft.icons.EVENT_NOTE_ROUNDED, color=COLORS['primary']),
                ft.Column(
                    [
                        ft.Text(event.get('title', 'Evento'), weight=ft.FontWeight.W_600),
                        ft.Text(meta, size=FONT_SIZES['body'], color=COLORS['secondary']),
                    ],
                    spacing=2,
                    tight=True,
                    expand=True,
                ),
                actions_row,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACING['sm'],
        )

        return ft.Card(
            elevation=CARD_ELEVATION,
            content=ft.Container(
                content=inner,
                border_radius=RADIUS_CARD,
                border=outline_border(),
                padding=ft.padding.symmetric(horizontal=SPACING['sm'], vertical=SPACING['xs']),
                on_click=open_event_detail,
            ),
        )

    def render_events_list():
        events_list.controls.clear()
        if not events_data:
            events_list.controls.append(
                EmptyState('Nenhum evento cadastrado.', icon=ft.icons.EVENT_BUSY)
            )
            return
        for event in events_data:
            events_list.controls.append(_build_event_object_card(event))

    async def handle_events_filter_change(_: ft.ControlEvent):
        loading_events.visible = True
        page.update()
        await load_events()

    async def load_all():
        await asyncio.gather(load_group(), load_events(), load_members(), load_songs())

    page.run_task(load_all)

    def go_to_members(_):
        page.go(f'/groups/{slug}/members')

    def go_to_songs(_):
        page.go(f'/groups/{slug}/songs')

    events_filter.on_change = handle_events_filter_change

    btn_add_member = PrimaryButton('Gerenciar membros', visible=False, expand=False)
    btn_add_member.on_click = go_to_members
    btn_add_song = PrimaryButton('Gerenciar músicas', visible=False, expand=False)
    btn_add_song.on_click = go_to_songs

    suggest_title_f = FormField(label='Título', dense=True)
    suggest_artist_f = FormField(label='Artista', dense=True)
    suggest_notes_f = FormField(label='Observações (opcional)', dense=True)
    suggest_link_f = FormField(label='Link de referência (opcional)', dense=True)
    suggest_key_dd = ft.Dropdown(
        label='Tonalidade (opcional)',
        expand=True,
        filled=True,
        border_radius=RADIUS_FIELD,
        options=[ft.dropdown.Option(text='(opcional)', key='')]
        + [ft.dropdown.Option(text=k, key=k) for k in TONALITIES],
        value='',
    )
    suggest_dlg_error = ft.Text('', color=COLORS['error'], size=FONT_SIZES['body'], visible=False)

    suggest_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text('Sugerir música'),
        content=ft.Container(
            content=ft.Column(
                [
                    suggest_title_f,
                    suggest_artist_f,
                    suggest_key_dd,
                    suggest_notes_f,
                    suggest_link_f,
                    suggest_dlg_error,
                ],
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                spacing=SPACING['sm'],
            ),
            padding=ft.padding.only(top=SPACING['sm']),
        ),
        actions=[
            ft.TextButton('Cancelar'),
            ft.FilledButton('Enviar'),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def close_suggest_dlg(_: ft.ControlEvent | None = None) -> None:
        suggest_dlg.open = False
        page.update()

    async def submit_suggest_dlg(_: ft.ControlEvent) -> None:
        suggest_dlg_error.visible = False
        if not suggest_title_f.value.strip():
            suggest_dlg_error.value = 'Título é obrigatório.'
            suggest_dlg_error.visible = True
            page.update()
            return
        client = APIClient(state, page)
        try:
            await create_song_suggestion(
                client,
                slug,
                title=suggest_title_f.value.strip(),
                artist=suggest_artist_f.value.strip(),
                key=(suggest_key_dd.value or '').strip(),
                notes=suggest_notes_f.value.strip(),
                link=suggest_link_f.value.strip(),
            )
            suggest_dlg.open = False
            page.update()
            suggest_title_f.value = ''
            suggest_artist_f.value = ''
            suggest_key_dd.value = ''
            suggest_notes_f.value = ''
            suggest_link_f.value = ''
            await load_songs()
        except APIError as ex:
            suggest_dlg_error.value = ex.message
            suggest_dlg_error.visible = True
            page.update()
        except Exception:
            suggest_dlg_error.value = 'Não foi possível enviar a sugestão.'
            suggest_dlg_error.visible = True
            page.update()

    suggest_dlg.actions[0].on_click = close_suggest_dlg
    suggest_dlg.actions[1].on_click = submit_suggest_dlg

    def open_suggest_dlg(_: ft.ControlEvent) -> None:
        suggest_dlg_error.visible = False
        page.dialog = suggest_dlg
        suggest_dlg.open = True
        page.update()

    btn_suggest_song = ft.OutlinedButton(
        'Sugerir música',
        icon=ft.icons.ADD_COMMENT_ROUNDED,
        visible=False,
        on_click=open_suggest_dlg,
    )

    manage_events_btn = PrimaryButton('Gerenciar eventos', visible=False, expand=False)
    manage_events_btn.on_click = go_to_events

    tab_eventos = ft.Tab(
        text='Eventos',
        icon=ft.icons.EVENT_NOTE_ROUNDED,
        content=ft.Container(
            content=ft.Column(
                [
                    SectionTitle('Eventos do grupo', trailing=events_filter_container),
                    loading_events,
                    events_list,
                    manage_events_btn,
                ],
                expand=True,
                spacing=SPACING['md'],
            ),
            expand=True,
            padding=ft.padding.only(top=SPACING['sm']),
        ),
    )

    tab_membros = ft.Tab(
        text='Membros',
        icon=ft.icons.PEOPLE_OUTLINE,
        content=ft.Container(
            content=ft.Column(
                [
                    SectionTitle('Membros do grupo'),
                    loading_members,
                    members_content,
                    btn_add_member,
                ],
                expand=True,
                spacing=SPACING['md'],
            ),
            expand=True,
            padding=ft.padding.only(top=SPACING['sm']),
        ),
    )

    tab_musicas = ft.Tab(
        text='Músicas',
        icon=ft.icons.QUEUE_MUSIC_ROUNDED,
        content=ft.Container(
            content=ft.Column(
                [
                    SectionTitle('Repertório'),
                    loading_songs,
                    songs_content,
                    ft.Row(
                        [btn_add_song, btn_suggest_song],
                        spacing=SPACING['sm'],
                        wrap=True,
                    ),
                ],
                expand=True,
                spacing=SPACING['md'],
            ),
            expand=True,
            padding=ft.padding.only(top=SPACING['sm']),
        ),
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[tab_eventos, tab_membros, tab_musicas],
        expand=True,
    )

    content = ft.Column(
        [
            group_title,
            error_msg,
            tabs,
        ],
        expand=True,
        spacing=SPACING['md'],
    )

    def go_back(_):
        page.go('/dashboard')

    return ft.View(
        f'/groups/{slug}',
        [
            ft.AppBar(
                title=ft.Text('Grupo'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
