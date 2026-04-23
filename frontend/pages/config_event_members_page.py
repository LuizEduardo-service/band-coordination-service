import asyncio
import flet as ft
from api.client import APIClient, APIError
from api.invites import create_event_invite
from authz import require_group_admin
from api.events import (
    get_event,
    list_event_members,
    add_event_member,
    update_event_member,
    remove_event_member,
)
from api.groups import get_members
from state.app_state import AppState
from components.styled import (
    StyledDropdown, FormField, PrimaryButton, ErrorText,
    PageContainer, SurfaceCard, EmptyState, SectionTitle,
)
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, RADIUS_FIELD
from instrument_icons import INSTRUMENT_OPTIONS, format_instruments_slugs


def build_config_event_members_page(page: ft.Page, state: AppState, slug: str, event_id: int) -> ft.View:
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)
    event_title = ft.Text('', size=FONT_SIZES['subtitle'], weight=ft.FontWeight.W_600)
    loading = ft.ProgressRing(visible=True)

    event_members_list = ft.Column(spacing=SPACING['sm'], expand=True, scroll=ft.ScrollMode.AUTO)
    group_members_dropdown = StyledDropdown('Membro do grupo', [], width=None)
    role_field = FormField('Função no evento (opcional)', width=None)
    add_button = PrimaryButton('Adicionar ao evento', width=None)

    dropdown_key_to_id: dict[str, int] = {}
    group_members_cache: list[dict] = []
    selected_add_instruments: set[str] = set()
    instrument_add_wrap = ft.Row(wrap=True, spacing=SPACING['sm'], run_spacing=SPACING['sm'], controls=[])

    # --- Invite dialog controls ---
    invite_search_field = ft.TextField(
        label='Buscar usuário',
        hint_text='Digite ao menos 2 caracteres...',
        prefix_icon=ft.icons.SEARCH_ROUNDED,
        filled=True,
        border_radius=RADIUS_FIELD,
    )
    invite_role_field = FormField('Papel no evento (opcional)', width=None)
    invite_results_col = ft.Column(spacing=SPACING['sm'])
    invite_search_task = None

    async def handle_invite_search(_: ft.ControlEvent) -> None:
        nonlocal invite_search_task
        q = invite_search_field.value.strip()
        if invite_search_task:
            invite_search_task.cancel()

        async def run():
            await asyncio.sleep(0.45)
            invite_results_col.controls.clear()
            if len(q) < 2:
                page.update()
                return
            client = APIClient(state, page)
            try:
                users = await client.get(f'/users/?search={q}')
            except Exception:
                error_msg.value = 'Erro ao buscar usuários.'
                error_msg.visible = True
                page.update()
                return
            if not users:
                invite_results_col.controls.append(
                    EmptyState('Nenhum usuário encontrado.', icon=ft.icons.PERSON_SEARCH_OUTLINED)
                )
            else:
                for user in users:
                    insts = list(user.get('instruments') or [])
                    uid = user['id']
                    uname = user['username']

                    async def send_invite(
                        _: ft.ControlEvent,
                        iid: int = uid,
                        instruments: list = insts,
                        name: str = uname,
                    ):
                        error_msg.visible = False
                        if not instruments:
                            error_msg.value = 'Este usuário não tem instrumentos no perfil.'
                            error_msg.visible = True
                            page.update()
                            return
                        cl = APIClient(state, page)
                        try:
                            await create_event_invite(
                                cl, slug, event_id, iid, instruments,
                                (invite_role_field.value or '').strip(),
                            )
                            success_msg.value = f'Convite enviado para {name}.'
                            success_msg.visible = True
                            close_invite_dlg(None)
                            await refresh_event_members()
                        except APIError as ex:
                            error_msg.value = ex.message
                            error_msg.visible = True
                            page.update()

                    invite_results_col.controls.append(
                        SurfaceCard(
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text(uname, weight=ft.FontWeight.W_500),
                                            ft.Text(
                                                format_instruments_slugs(insts),
                                                size=FONT_SIZES['body'],
                                                color=COLORS['secondary'],
                                            ),
                                        ],
                                        expand=True,
                                    ),
                                    ft.FilledTonalButton('Convidar', on_click=send_invite),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=SPACING['sm'],
                        )
                    )
            page.update()

        invite_search_task = asyncio.create_task(run())

    invite_search_field.on_change = handle_invite_search

    invite_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text('Convidar para este culto'),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Usuário deve estar cadastrado no sistema e ter instrumentos no perfil.',
                        size=FONT_SIZES['body'],
                        color=COLORS['secondary'],
                    ),
                    invite_search_field,
                    invite_role_field,
                    invite_results_col,
                ],
                spacing=SPACING['md'],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.only(top=SPACING['sm']),
        ),
        actions=[ft.TextButton('Fechar', on_click=lambda _: close_invite_dlg(_))],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_invite_dlg(_):
        invite_search_field.value = ''
        invite_role_field.value = ''
        invite_results_col.controls.clear()
        page.dialog = invite_dlg
        invite_dlg.open = True
        page.update()

    def close_invite_dlg(_):
        invite_dlg.open = False
        page.update()

    # --- Instrument chips for add form ---
    def rebuild_add_chips() -> None:
        instrument_add_wrap.controls.clear()
        selected_add_instruments.clear()
        key = group_members_dropdown.value
        mid = dropdown_key_to_id.get(key or '')
        m = next((x for x in group_members_cache if x['id'] == mid), None)
        if not m:
            page.update()
            return
        user_inst = m['user'].get('instruments') or []
        if not user_inst:
            instrument_add_wrap.controls.append(
                ft.Text(
                    'Usuário sem instrumentos no perfil.',
                    color=COLORS['error'],
                    size=FONT_SIZES['body'],
                )
            )
            page.update()
            return
        for inst_slug, label, icon in INSTRUMENT_OPTIONS:
            if inst_slug not in user_inst:
                continue
            selected_add_instruments.add(inst_slug)

            def on_chip_select(e: ft.ControlEvent, s: str = inst_slug) -> None:
                chip = e.control
                if s in selected_add_instruments:
                    selected_add_instruments.remove(s)
                    chip.selected = False
                else:
                    selected_add_instruments.add(s)
                    chip.selected = True
                page.update()

            instrument_add_wrap.controls.append(
                ft.Chip(
                    label=ft.Text(label),
                    leading=ft.Icon(icon, size=16),
                    selected=True,
                    data=inst_slug,
                    on_select=on_chip_select,
                    show_checkmark=True,
                )
            )
        page.update()

    group_members_dropdown.on_change = lambda _: rebuild_add_chips()

    # --- Member row builder ---
    def _instrument_icon_row(slugs: list) -> ft.Row:
        icons = [
            ft.Icon(icon, size=20, color=COLORS['primary'])
            for inst_slug, _label, icon in INSTRUMENT_OPTIONS
            if inst_slug in (slugs or [])
        ]
        return ft.Row(icons, spacing=SPACING['xs']) if icons else ft.Text('—', size=FONT_SIZES['body'])

    def _build_member_row(member: dict) -> ft.Container:
        membership = member.get('membership') or {}
        user = membership.get('user') or {}
        username = user.get('username') or member.get('guest_user', {}).get('username', '—')
        group_role = membership.get('role', 'convidado')
        user_inst = user.get('instruments') or []

        role_inline = ft.TextField(
            value=member.get('role_in_event') or '',
            label='Função no evento',
            filled=True,
            border_radius=RADIUS_FIELD,
            expand=True,
        )
        participation_inline = ft.Dropdown(
            label='Participação',
            filled=True,
            border_radius=RADIUS_FIELD,
            value=member.get('participation', 'pending'),
            width=160,
            options=[
                ft.dropdown.Option(key='pending', text='Pendente'),
                ft.dropdown.Option(key='confirmed', text='Confirmado'),
                ft.dropdown.Option(key='declined', text='Recusado'),
            ],
        )

        evt_selected: set[str] = set(member.get('instruments') or [])
        edit_chips: list[ft.Chip] = []

        for inst_slug, label, icon in INSTRUMENT_OPTIONS:
            if inst_slug not in user_inst:
                continue

            def on_edit_chip(e: ft.ControlEvent, s: str = inst_slug) -> None:
                chip = e.control
                if s in evt_selected:
                    evt_selected.remove(s)
                    chip.selected = False
                else:
                    evt_selected.add(s)
                    chip.selected = True
                page.update()

            edit_chips.append(
                ft.Chip(
                    label=ft.Text(label),
                    leading=ft.Icon(icon, size=16),
                    selected=inst_slug in evt_selected,
                    data=inst_slug,
                    on_select=on_edit_chip,
                    show_checkmark=True,
                )
            )

        async def on_save(_: ft.ControlEvent):
            error_msg.visible = False
            success_msg.visible = False
            if not evt_selected:
                error_msg.value = 'Selecione ao menos um instrumento.'
                error_msg.visible = True
                page.update()
                return
            client = APIClient(state, page)
            try:
                await update_event_member(client, slug, event_id, member['id'], {
                    'role_in_event': (role_inline.value or '').strip(),
                    'participation': participation_inline.value or 'pending',
                    'instruments': sorted(evt_selected),
                })
                success_msg.value = 'Membro atualizado.'
                success_msg.visible = True
                await refresh_event_members()
            except APIError as ex:
                error_msg.value = ex.message
                error_msg.visible = True
                page.update()

        async def on_remove(_: ft.ControlEvent):
            error_msg.visible = False
            success_msg.visible = False
            client = APIClient(state, page)
            try:
                await remove_event_member(client, slug, event_id, member['id'])
                success_msg.value = 'Membro removido.'
                success_msg.visible = True
                await refresh_event_members()
            except APIError as ex:
                error_msg.value = ex.message
                error_msg.visible = True
                page.update()

        return SurfaceCard(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(username, weight=ft.FontWeight.W_600),
                                    ft.Text(
                                        f'Papel no grupo: {group_role}',
                                        size=FONT_SIZES['body'],
                                        color=COLORS['secondary'],
                                    ),
                                ],
                                expand=True,
                            ),
                            _instrument_icon_row(member.get('instruments') or []),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        'Instrumentos neste evento',
                        size=FONT_SIZES['label'],
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=SPACING['sm'],
                        run_spacing=SPACING['sm'],
                        controls=edit_chips if edit_chips else [
                            ft.Text('Sem instrumentos disponíveis.', color=COLORS['secondary'], size=FONT_SIZES['body'])
                        ],
                    ),
                    ft.Row(
                        [role_inline, participation_inline],
                        spacing=SPACING['sm'],
                    ),
                    ft.Row(
                        [
                            ft.FilledTonalButton('Salvar', icon=ft.icons.CHECK_ROUNDED, on_click=on_save),
                            ft.TextButton('Remover', icon=ft.icons.DELETE_OUTLINE, on_click=on_remove),
                        ],
                        spacing=SPACING['sm'],
                    ),
                ],
                spacing=SPACING['sm'],
            ),
            padding=SPACING['md'],
        )

    # --- Add member handler ---
    async def handle_add(_: ft.ControlEvent):
        error_msg.visible = False
        success_msg.visible = False
        add_button.disabled = True
        page.update()

        selected_key = group_members_dropdown.value
        membership_id = dropdown_key_to_id.get(selected_key or '')
        if not membership_id:
            error_msg.value = 'Selecione um membro do grupo.'
            error_msg.visible = True
            add_button.disabled = False
            page.update()
            return
        if not selected_add_instruments:
            error_msg.value = 'Selecione ao menos um instrumento.'
            error_msg.visible = True
            add_button.disabled = False
            page.update()
            return
        client = APIClient(state, page)
        try:
            await add_event_member(
                client, slug, event_id, membership_id,
                instruments=sorted(selected_add_instruments),
                role_in_event=(role_field.value or '').strip(),
            )
            success_msg.value = 'Membro adicionado ao evento.'
            success_msg.visible = True
            role_field.value = ''
            group_members_dropdown.value = None
            await load_context()
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao adicionar membro.'
            error_msg.visible = True
        finally:
            add_button.disabled = False
            page.update()

    add_button.on_click = handle_add

    # --- Load ---
    async def load_context():
        nonlocal group_members_cache
        if not await require_group_admin(page, state, slug):
            loading.visible = False
            page.update()
            return
        error_msg.visible = False
        loading.visible = True
        event_members_list.controls.clear()
        page.update()
        client = APIClient(state, page)
        try:
            event, group_members, event_members_data = await asyncio.gather(
                get_event(client, slug, event_id),
                get_members(client, slug),
                list_event_members(client, slug, event_id),
            )
            event_title.value = event.get('title', f'Evento {event_id}')

            group_members_cache = list(group_members)
            dropdown_key_to_id.clear()
            options = []
            for m in group_members:
                key = f"{m['user']['username']} ({m['role']})"
                dropdown_key_to_id[key] = m['id']
                options.append(ft.dropdown.Option(text=key, key=key))
            group_members_dropdown.options = options

            event_members = event_members_data
            if not event_members:
                event_members_list.controls.append(
                    EmptyState('Nenhum membro associado ao evento.', icon=ft.icons.PEOPLE_OUTLINE)
                )
            else:
                for member in event_members:
                    event_members_list.controls.append(_build_member_row(member))
            rebuild_add_chips()
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao carregar membros do evento.'
            error_msg.visible = True
        finally:
            loading.visible = False
            page.update()

    async def refresh_event_members():
        client = APIClient(state, page)
        try:
            members = await list_event_members(client, slug, event_id)
            event_members_list.controls.clear()
            if not members:
                event_members_list.controls.append(
                    EmptyState('Nenhum membro associado ao evento.', icon=ft.icons.PEOPLE_OUTLINE)
                )
            else:
                for m in members:
                    event_members_list.controls.append(_build_member_row(m))
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
        page.update()

    page.run_task(load_context)

    # --- Layout ---
    add_panel = SurfaceCard(
        ft.Column(
            [
                ft.Text('Adicionar membro do grupo', weight=ft.FontWeight.W_600),
                group_members_dropdown,
                ft.Text(
                    'Instrumentos neste culto',
                    size=FONT_SIZES['label'],
                    weight=ft.FontWeight.W_500,
                ),
                instrument_add_wrap,
                role_field,
                add_button,
            ],
            spacing=SPACING['md'],
        ),
        padding=SPACING['md'],
    )

    invite_btn = ft.OutlinedButton(
        'Convidar fora do grupo',
        icon=ft.icons.PERSON_ADD_ALT_1_ROUNDED,
        on_click=open_invite_dlg,
    )

    content = ft.Column(
        [
            event_title,
            error_msg,
            success_msg,
            SectionTitle('Membros do evento', trailing=invite_btn),
            loading,
            SurfaceCard(event_members_list, padding=SPACING['sm'], expand=1),
            SectionTitle('Adicionar membro do grupo'),
            add_panel,
        ],
        expand=True,
        spacing=SPACING['md'],
    )

    def go_back(_: ft.ControlEvent):
        page.go(f'/groups/{slug}/events')

    return ft.View(
        f'/groups/{slug}/events/{event_id}/members',
        [
            ft.AppBar(
                title=ft.Text('Membros do evento'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
