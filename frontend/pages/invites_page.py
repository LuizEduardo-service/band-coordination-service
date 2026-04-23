import flet as ft
from api.client import APIClient, APIError
from api.invites import list_invites, accept_invite, decline_invite
from api.song_suggestions import (
    list_pending_song_suggestions,
    approve_song_suggestion,
    reject_song_suggestion,
)
from state.app_state import AppState
from components.styled import PageContainer, ErrorText, PrimaryButton
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, RADIUS_SURFACE, outline_border


def build_invites_page(page: ft.Page, state: AppState) -> ft.View:
    loading = ft.ProgressRing(visible=True)
    error_msg = ErrorText()
    body = ft.Column(spacing=SPACING['md'], scroll=ft.ScrollMode.AUTO, expand=True)

    def go_back(_: ft.ControlEvent) -> None:
        page.go('/dashboard')

    async def load() -> None:
        client = APIClient(state, page)
        loading.visible = True
        error_msg.visible = False
        body.controls.clear()
        page.update()

        invite_items: list = []
        suggestions: list = []
        invite_err: str | None = None
        sug_err: str | None = None

        try:
            invite_items = await list_invites(client, status='pending')
        except APIError as ex:
            invite_err = ex.detail if isinstance(ex.detail, str) else str(ex.detail)
        except Exception:
            invite_err = 'Não foi possível carregar convites.'

        try:
            suggestions = await list_pending_song_suggestions(client)
        except APIError as ex:
            sug_err = ex.detail if isinstance(ex.detail, str) else str(ex.detail)
        except Exception:
            sug_err = 'Não foi possível carregar sugestões de músicas.'

        loading.visible = False
        if invite_err and sug_err:
            error_msg.value = invite_err if invite_err == sug_err else f'{invite_err} / {sug_err}'
            error_msg.visible = True
            page.update()
            return

        body.controls.append(
            ft.Text(
                'Convites',
                weight=ft.FontWeight.W_600,
                size=FONT_SIZES['label'],
                color=COLORS['primary'],
            )
        )

        if invite_err:
            body.controls.append(
                ft.Text(invite_err, color=COLORS['error'], size=FONT_SIZES['body'])
            )
        elif not invite_items:
            body.controls.append(
                ft.Text('Nenhum convite pendente.', color=COLORS['secondary'], size=FONT_SIZES['body'])
            )
        else:
            for inv in invite_items:
                iid = inv['id']
                kind = inv.get('kind', '')
                title = (
                    f"Grupo: {inv.get('group_name') or '—'}"
                    if kind == 'group'
                    else f"Evento: {inv.get('event_title') or '—'}"
                )
                inviter = (inv.get('inviter') or {}).get('username') or '—'
                slug = inv.get('group_slug') or ''
                event_id = inv.get('event_id')

                async def do_accept(_: ft.ControlEvent, pk: int = iid):
                    try:
                        await accept_invite(client, pk)
                        await load()
                        page.go('/dashboard')
                    except APIError as ex:
                        error_msg.value = ex.detail if isinstance(ex.detail, str) else str(ex.detail)
                        error_msg.visible = True
                        page.update()

                async def do_decline(_: ft.ControlEvent, pk: int = iid):
                    try:
                        await decline_invite(client, pk)
                        await load()
                    except APIError as ex:
                        error_msg.value = ex.detail if isinstance(ex.detail, str) else str(ex.detail)
                        error_msg.visible = True
                        page.update()

                def open_event(_: ft.ControlEvent, s: str = slug, eid: int | None = event_id):
                    if s and eid is not None:
                        page.go(f'/groups/{s}/events/{eid}')

                accept_btn = PrimaryButton('Aceitar', width=120)
                accept_btn.on_click = do_accept
                decline_btn = ft.OutlinedButton('Recusar', width=120, on_click=do_decline)
                actions = ft.Row(
                    [accept_btn, decline_btn],
                    spacing=SPACING['sm'],
                )
                extra = None
                if kind == 'event' and slug and event_id is not None:
                    extra = ft.TextButton('Ver evento', on_click=open_event)

                card = ft.Card(
                    content=ft.Container(
                        padding=SPACING['md'],
                        content=ft.Column(
                            [
                                ft.Text(title, weight=ft.FontWeight.W_600, size=FONT_SIZES['label']),
                                ft.Text(
                                    f'Convidado por {inviter}',
                                    size=FONT_SIZES['body'],
                                    color=COLORS['secondary'],
                                ),
                                actions,
                                extra if extra else ft.Container(height=0),
                            ],
                            spacing=SPACING['sm'],
                            tight=True,
                        ),
                    )
                )
                body.controls.append(card)

        body.controls.append(ft.Container(height=SPACING['md']))
        body.controls.append(
            ft.Text(
                'Sugestões de músicas',
                weight=ft.FontWeight.W_600,
                size=FONT_SIZES['label'],
                color=COLORS['primary'],
            )
        )

        if sug_err:
            body.controls.append(
                ft.Text(sug_err, color=COLORS['error'], size=FONT_SIZES['body'])
            )
        elif not suggestions:
            body.controls.append(
                ft.Text(
                    'Nenhuma sugestão pendente.',
                    color=COLORS['secondary'],
                    size=FONT_SIZES['body'],
                )
            )
        else:
            for s in suggestions:
                sid = s['id']
                gname = s.get('group_name') or '—'
                stitle = s.get('title') or '—'
                artist = (s.get('artist') or '').strip() or '—'
                key_disp = (s.get('key_display') or '').strip() or '—'
                notes = (s.get('notes') or '').strip() or '—'
                link_val = (s.get('link') or '').strip()
                sug_user = (s.get('suggested_by') or {}).get('username') or '—'

                async def do_approve(_: ft.ControlEvent, pk: int = sid):
                    try:
                        await approve_song_suggestion(client, pk)
                        await load()
                    except APIError as ex:
                        error_msg.value = ex.detail if isinstance(ex.detail, str) else str(ex.detail)
                        error_msg.visible = True
                        page.update()

                async def do_reject(_: ft.ControlEvent, pk: int = sid):
                    try:
                        await reject_song_suggestion(client, pk)
                        await load()
                    except APIError as ex:
                        error_msg.value = ex.detail if isinstance(ex.detail, str) else str(ex.detail)
                        error_msg.visible = True
                        page.update()

                def make_open_link(url: str):
                    def _open(_: ft.ControlEvent):
                        if url and page.web:
                            page.launch_url(url)

                    return _open

                approve_btn = PrimaryButton('Aprovar', width=120)
                approve_btn.on_click = do_approve
                reject_btn = ft.OutlinedButton('Recusar', width=120, on_click=do_reject)
                actions_row = ft.Row([approve_btn, reject_btn], spacing=SPACING['sm'])

                detail_inner = ft.Column(
                    [
                        ft.Text(f'Grupo: {gname}', size=FONT_SIZES['body']),
                        ft.Text(f'Título: {stitle}', size=FONT_SIZES['body']),
                        ft.Text(f'Artista: {artist}', size=FONT_SIZES['body']),
                        ft.Text(f'Tonalidade: {key_disp}', size=FONT_SIZES['body']),
                        ft.Text(f'Observações: {notes}', size=FONT_SIZES['body']),
                        ft.TextButton(
                            'Abrir link',
                            visible=bool(link_val),
                            on_click=make_open_link(link_val),
                        ),
                        actions_row,
                    ],
                    spacing=SPACING['xs'],
                    tight=True,
                )

                tile = ft.ExpansionTile(
                    title=ft.Text(f'{stitle} — {gname}', weight=ft.FontWeight.W_600),
                    subtitle=ft.Text(f'Sugerido por {sug_user}', color=COLORS['secondary']),
                    controls=[
                        ft.Container(
                            padding=ft.padding.only(
                                left=SPACING['md'],
                                right=SPACING['md'],
                                bottom=SPACING['md'],
                            ),
                            content=detail_inner,
                        ),
                    ],
                )
                body.controls.append(ft.Card(content=tile))

        page.update()

    page.run_task(load)

    content = ft.Column(
        [
            loading,
            error_msg,
            ft.Container(
                content=body,
                padding=SPACING['md'],
                bgcolor=COLORS['surface_container'],
                border_radius=RADIUS_SURFACE,
                border=outline_border(),
                expand=True,
            ),
        ],
        expand=True,
        spacing=SPACING['md'],
    )

    return ft.View(
        '/invites',
        [
            ft.AppBar(
                title=ft.Text('Notificações'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
