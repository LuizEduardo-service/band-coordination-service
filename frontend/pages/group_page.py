import flet as ft
from datetime import datetime
from api.client import APIClient, APIError
from api.song_suggestions import create_song_suggestion
from state.app_state import AppState
from components.styled import PageContainer, ErrorText, EmptyState, SectionTitle, PrimaryButton, FormField
from constants import TONALITIES
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, CARD_ELEVATION, RADIUS_CARD, RADIUS_FIELD, outline_border
from instrument_icons import format_instruments_slugs


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
        label='Filtro de eventos',
        width=220,
        value='all',
        filled=True,
        border_radius=RADIUS_FIELD,
        options=[
            ft.dropdown.Option(key='all', text='Todos'),
            ft.dropdown.Option(key='upcoming', text='Próximos'),
            ft.dropdown.Option(key='past', text='Passados'),
        ],
    )

    events_data: list[dict] = []

    def format_event_date(value: str) -> str:
        if not value:
            return '-'
        try:
            normalized = value.replace('Z', '+00:00')
            dt = datetime.fromisoformat(normalized)
            return dt.strftime('%d/%m/%Y %H:%M')
        except Exception:
            return value

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
            error_msg.value = f"Erro ao carregar grupo: {ex.detail}"
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
            error_msg.value = f"Erro ao carregar membros: {ex.detail}"
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
            error_msg.value = f"Erro ao carregar músicas: {ex.detail}"
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
            error_msg.value = f"Erro ao carregar eventos: {ex.detail}"
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

        desc = (event.get('description') or '').strip() or 'Sem descrição'
        meta = (
            f"{format_event_date(event.get('date', ''))}  ·  "
            f"Membros: {event.get('member_count', 0)}  ·  "
            f"Músicas: {event.get('song_count', 0)}"
        )

        actions_row = ft.Row(
            [
                ft.FilledTonalButton(
                    'Detalhes',
                    icon=ft.icons.EVENT_ROUNDED,
                    on_click=open_event_detail,
                ),
                ft.OutlinedButton(
                    'Membros',
                    icon=ft.icons.GROUP_OUTLINED,
                    on_click=open_event_members,
                    visible=user_is_group_admin,
                ),
                ft.OutlinedButton(
                    'Setlist',
                    icon=ft.icons.QUEUE_MUSIC_ROUNDED,
                    on_click=open_event_songs,
                    visible=user_is_group_admin,
                ),
            ],
            spacing=SPACING['sm'],
            wrap=True,
        )

        inner = ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.icons.EVENT_NOTE_ROUNDED, color=COLORS['primary']),
                    title=ft.Text(event.get('title', 'Evento'), weight=ft.FontWeight.W_600),
                    subtitle=ft.Column(
                        [
                            ft.Text(meta, size=FONT_SIZES['body'], color=COLORS['secondary']),
                            ft.Text(
                                desc,
                                size=FONT_SIZES['body'],
                                max_lines=3,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=SPACING['xs'],
                        tight=True,
                    ),
                    on_click=open_event_detail,
                ),
                ft.Container(content=actions_row, padding=ft.padding.only(left=SPACING['md'], right=SPACING['md'], bottom=SPACING['md'])),
            ],
            spacing=0,
        )

        return ft.Card(
            elevation=CARD_ELEVATION,
            content=ft.Container(
                content=inner,
                border_radius=RADIUS_CARD,
                border=outline_border(),
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

    page.run_task(load_group)
    page.run_task(load_events)
    page.run_task(load_members)
    page.run_task(load_songs)

    def go_to_members(_):
        page.go(f'/groups/{slug}/members')

    def go_to_songs(_):
        page.go(f'/groups/{slug}/songs')

    events_filter.on_change = handle_events_filter_change

    btn_add_member = PrimaryButton('Gerenciar membros', width=None, visible=False)
    btn_add_member.on_click = go_to_members
    btn_add_song = PrimaryButton('Gerenciar músicas', width=None, visible=False)
    btn_add_song.on_click = go_to_songs

    suggest_title_f = FormField(label='Título', width=320, dense=True)
    suggest_artist_f = FormField(label='Artista', width=320, dense=True)
    suggest_notes_f = FormField(label='Observações (opcional)', width=320, dense=True)
    suggest_link_f = FormField(label='Link de referência (opcional)', width=320, dense=True)
    suggest_key_dd = ft.Dropdown(
        label='Tonalidade (opcional)',
        width=320,
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
            width=360,
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
            suggest_dlg_error.value = ex.detail if isinstance(ex.detail, str) else str(ex.detail)
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

    manage_events_btn = ft.OutlinedButton(
        'Gerenciar eventos',
        on_click=go_to_events,
        icon=ft.icons.EDIT_CALENDAR_ROUNDED,
        visible=False,
    )

    tab_eventos = ft.Tab(
        text='Eventos',
        icon=ft.icons.EVENT_NOTE_ROUNDED,
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [manage_events_btn],
                        alignment=ft.MainAxisAlignment.END,
                        expand=True,
                    ),
                    ft.Row(
                        [events_filter],
                        wrap=True,
                    ),
                    loading_events,
                    events_list,
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
