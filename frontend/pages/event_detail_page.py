import asyncio
import flet as ft
from datetime import datetime

from api.client import APIClient, APIError
from api.events import get_event, update_participation
from api.groups import get_group
from state.app_state import AppState
from components.styled import PageContainer, ErrorText, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, RADIUS_SURFACE, outline_border
from instrument_icons import format_instruments_slugs

_PARTICIPATION_LABELS = {
    'pending': 'Pendente',
    'confirmed': 'Confirmado',
    'declined': 'Recusado',
}


def _participation_icon(code: str | None) -> tuple[str, str]:
    """Retorna (nome_do_icone, cor) para o status de participação."""
    c = (code or '').strip()
    if c == 'confirmed':
        return ft.icons.CHECK_CIRCLE_ROUNDED, COLORS['success']
    if c == 'declined':
        return ft.icons.CANCEL_ROUNDED, COLORS['error']
    return ft.icons.SCHEDULE_ROUNDED, COLORS['secondary']


def _format_event_date(value: str) -> str:
    if not value:
        return '-'
    try:
        normalized = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(normalized)
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return value


def build_event_detail_page(page: ft.Page, state: AppState, slug: str, event_id: int) -> ft.View:
    loading = ft.ProgressRing(visible=True)
    error_msg = ErrorText()
    body = ft.Column(spacing=SPACING['md'], scroll=ft.ScrollMode.AUTO, expand=True)

    def go_back(_: ft.ControlEvent) -> None:
        page.go(f'/groups/{slug}')

    def open_members(_: ft.ControlEvent) -> None:
        page.go(f'/groups/{slug}/events/{event_id}/members')

    def open_songs(_: ft.ControlEvent) -> None:
        page.go(f'/groups/{slug}/events/{event_id}/songs')

    participation_hint = ft.Text('', size=FONT_SIZES['label'], color=COLORS['success'], visible=False)

    admin_actions_row = ft.Row(
        [
            ft.OutlinedButton('Membros do evento', icon=ft.icons.PEOPLE_OUTLINE, on_click=open_members),
            ft.OutlinedButton('Setlist', icon=ft.icons.QUEUE_MUSIC_ROUNDED, on_click=open_songs),
        ],
        spacing=SPACING['sm'],
        wrap=True,
        visible=False,
    )

    async def load() -> None:
        client = APIClient(state, page)
        try:
            group_meta, ev = await asyncio.gather(
                get_group(client, slug),
                get_event(client, slug, event_id),
            )
        except APIError as ex:
            loading.visible = False
            error_msg.value = ex.detail
            error_msg.visible = True
            page.update()
            return
        except Exception:
            loading.visible = False
            error_msg.value = 'Não foi possível carregar o evento.'
            error_msg.visible = True
            page.update()
            return

        loading.visible = False
        body.controls.clear()

        is_admin = group_meta.get('my_role') == 'admin'
        admin_actions_row.visible = bool(is_admin)
        my_username = (state.user or {}).get('username') or ''

        created = ev.get('created_by')
        meta_parts: list[str] = []
        if created and isinstance(created, dict):
            uname = created.get('username') or ''
            if uname:
                meta_parts.append(f'Criado por {uname}')
        created_at = ev.get('created_at')
        if created_at:
            meta_parts.append(f'Cadastro: {_format_event_date(created_at)}')

        body.controls.extend(
            [
                ft.Text(ev.get('title') or 'Evento', size=FONT_SIZES['subtitle'], weight=ft.FontWeight.W_600),
                ft.Text(_format_event_date(ev.get('date', '')), size=FONT_SIZES['body'], color=COLORS['secondary']),
                ft.Text(
                    ev.get('description') or 'Sem descrição.',
                    size=FONT_SIZES['body'],
                    selectable=True,
                ),
            ]
        )
        if meta_parts:
            body.controls.append(
                ft.Text(' • '.join(meta_parts), size=FONT_SIZES['label'], color=COLORS['secondary'])
            )

        body.controls.append(admin_actions_row)

        participation_hint.visible = False
        participation_hint.value = ''
        participation_hint.color = COLORS['success']
        body.controls.append(participation_hint)

        members = ev.get('event_members') or []
        body.controls.append(SectionTitle('Equipe neste evento'))
        if not members:
            body.controls.append(ft.Text('Nenhum membro escalado ainda.', color=COLORS['secondary']))
        else:
            for m in members:
                user = m.get('user') or (m.get('membership') or {}).get('user') or {}
                username = user.get('username', '?')
                role = (m.get('role_in_event') or '').strip()
                pcode = m.get('participation') or ''
                picon, pcolor = _participation_icon(pcode)
                hint = _PARTICIPATION_LABELS.get(pcode, pcode or _PARTICIPATION_LABELS['pending'])
                inst = format_instruments_slugs(m.get('instruments'))
                sub_parts: list[str] = []
                if role:
                    sub_parts.append(role)
                if inst:
                    sub_parts.append(inst)
                sub = ' • '.join(sub_parts)
                is_me = my_username and username == my_username
                trailing: ft.Control | None = None
                if is_me and not is_admin:
                    member_id = m['id']
                    cur = pcode or 'pending'
                    last_local = {'v': cur}

                    async def persist_participation(new_v: str) -> None:
                        if new_v == last_local['v']:
                            return
                        participation_hint.visible = False
                        page.update()
                        try:
                            await update_participation(client, slug, event_id, member_id, new_v)
                            last_local['v'] = new_v
                            await load()
                            participation_hint.color = COLORS['success']
                            participation_hint.value = 'Participação atualizada.'
                            participation_hint.visible = True
                        except APIError as ex:
                            participation_hint.value = str(ex.detail)
                            participation_hint.visible = True
                            participation_hint.color = COLORS['error']
                        except Exception:
                            participation_hint.value = 'Não foi possível salvar.'
                            participation_hint.visible = True
                            participation_hint.color = COLORS['error']
                        page.update()

                    async def on_thumb_up(_: ft.ControlEvent) -> None:
                        new_v = 'pending' if last_local['v'] == 'confirmed' else 'confirmed'
                        await persist_participation(new_v)

                    async def on_thumb_down(_: ft.ControlEvent) -> None:
                        new_v = 'pending' if last_local['v'] == 'declined' else 'declined'
                        await persist_participation(new_v)

                    btn_up = ft.IconButton(
                        icon=ft.icons.THUMB_UP_OFF_ALT_ROUNDED,
                        selected_icon=ft.icons.THUMB_UP_ROUNDED,
                        selected=cur == 'confirmed',
                        icon_color=COLORS['secondary'],
                        selected_icon_color=COLORS['success'],
                        icon_size=26,
                        tooltip='Confirmo (toque de novo para ficar pendente)',
                        on_click=on_thumb_up,
                    )
                    btn_down = ft.IconButton(
                        icon=ft.icons.THUMB_DOWN_OFF_ALT_ROUNDED,
                        selected_icon=ft.icons.THUMB_DOWN_ROUNDED,
                        selected=cur == 'declined',
                        icon_color=COLORS['secondary'],
                        selected_icon_color=COLORS['error'],
                        icon_size=26,
                        tooltip='Não poderei (toque de novo para pendente)',
                        on_click=on_thumb_down,
                    )
                    trailing = ft.Row(
                        [btn_up, btn_down],
                        tight=True,
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                body.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(picon, color=pcolor, size=26, tooltip=hint),
                        title=ft.Text(username, weight=ft.FontWeight.W_500),
                        subtitle=ft.Text(sub, color=COLORS['secondary'], size=FONT_SIZES['label'])
                        if sub
                        else None,
                        trailing=trailing,
                    )
                )

        songs_raw = ev.get('event_songs') or []
        songs_sorted = sorted(songs_raw, key=lambda x: (x.get('order') is None, x.get('order', 0)))
        body.controls.append(SectionTitle('Setlist'))
        if not songs_sorted:
            body.controls.append(ft.Text('Nenhuma música na ordem do culto.', color=COLORS['secondary']))
        else:
            for es in songs_sorted:
                song = es.get('song') or {}
                title = song.get('title', 'Música')
                artist = song.get('artist') or ''
                key = song.get('key_display') or song.get('key') or ''
                line_meta = f'{artist} • {key}' if artist and key else (artist or key or '')
                added_by = es.get('added_by')
                picker = ''
                if isinstance(added_by, dict):
                    picker = (added_by.get('username') or '').strip()
                sub_controls: list[ft.Control] = []
                if line_meta:
                    sub_controls.append(
                        ft.Text(line_meta, size=FONT_SIZES['body'], color=COLORS['secondary']),
                    )
                if picker:
                    sub_controls.append(
                        ft.Text(f'Incluída por {picker}', size=FONT_SIZES['body'], color=COLORS['secondary']),
                    )
                subtitle = ft.Column(sub_controls, spacing=SPACING['xs']) if sub_controls else None
                body.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.MUSIC_NOTE_ROUNDED, color=COLORS['primary'], size=20),
                        title=ft.Text(title, size=FONT_SIZES['body'], weight=ft.FontWeight.W_500),
                        subtitle=subtitle,
                    )
                )

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
        f'/groups/{slug}/events/{event_id}',
        [
            ft.AppBar(
                title=ft.Text('Detalhes do evento'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
