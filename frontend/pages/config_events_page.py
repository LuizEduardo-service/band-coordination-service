import flet as ft
from datetime import datetime, time
from api.client import APIClient, APIError
from utils.date_utils import format_event_date
from api.events import list_events, create_event, update_event, delete_event
from authz import require_group_admin
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, PageContainer, SurfaceCard, EmptyState, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, RADIUS_FIELD


def _parse_api_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
    except ValueError:
        return None



def build_config_events_page(page: ft.Page, state: AppState, slug: str) -> ft.View:
    events_list = ft.Column(spacing=SPACING['sm'], expand=True, scroll=ft.ScrollMode.AUTO)
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)
    loading = ft.ProgressRing(visible=True)

    # --- Form state ---
    title_field = FormField(label='Título do evento')
    description_field = FormField(label='Descrição (opcional)')
    editing_event_id: list[int | None] = [None]
    event_dt_state: dict[str, datetime | None] = {'dt': None}

    form_error = ErrorText()

    date_display = ft.TextField(
        label='Data e hora do evento',
        hint_text='Use os botões para escolher',
        read_only=True,
        filled=True,
        border_radius=RADIUS_FIELD,
        expand=True,
    )

    def sync_date_display() -> None:
        dt = event_dt_state['dt']
        date_display.value = dt.strftime('%d/%m/%Y %H:%M') if dt else ''

    now = datetime.now()
    first_cal = datetime(now.year - 2, 1, 1)
    last_cal = datetime(now.year + 5, 12, 31)

    def on_date_picked(_: ft.ControlEvent) -> None:
        picked = date_picker.value
        if picked is None:
            return
        cur = event_dt_state['dt']
        t = cur.time() if cur else time(19, 0)
        event_dt_state['dt'] = datetime.combine(picked.date(), t)
        sync_date_display()
        page.update()

    def on_time_picked(_: ft.ControlEvent) -> None:
        t = time_picker.value
        if t is None:
            return
        cur = event_dt_state['dt']
        d = cur.date() if cur else datetime.now().date()
        event_dt_state['dt'] = datetime.combine(d, t)
        sync_date_display()
        page.update()

    date_picker = ft.DatePicker(
        first_date=first_cal,
        last_date=last_cal,
        help_text='Data do evento',
        field_hint_text='dd/mm/aaaa',
        confirm_text='OK',
        cancel_text='Cancelar',
        on_change=on_date_picked,
    )
    time_picker = ft.TimePicker(
        help_text='Horário de início',
        confirm_text='OK',
        cancel_text='Cancelar',
        on_change=on_time_picked,
    )

    for c in list(page.overlay):
        if isinstance(c, (ft.DatePicker, ft.TimePicker)):
            page.overlay.remove(c)
    page.overlay.append(date_picker)
    page.overlay.append(time_picker)

    def open_date_picker(_: ft.ControlEvent) -> None:
        base = event_dt_state['dt'] or datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        date_picker.value = base
        date_picker.pick_date()

    def open_time_picker(_: ft.ControlEvent) -> None:
        base = event_dt_state['dt'] or datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        time_picker.value = base.time()
        time_picker.pick_time()

    date_time_row = ft.Row(
        [
            date_display,
            ft.OutlinedButton('Data', icon=ft.icons.CALENDAR_MONTH, on_click=open_date_picker),
            ft.OutlinedButton('Horário', icon=ft.icons.SCHEDULE, on_click=open_time_picker),
        ],
        spacing=SPACING['sm'],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    save_button = PrimaryButton('Criar evento', expand=False)

    # --- Dialog ---
    event_dlg = ft.AlertDialog(
        modal=True,
        content=ft.Container(
            content=ft.Column(
                [
                    form_error,
                    title_field,
                    date_time_row,
                    description_field,
                ],
                spacing=SPACING['md'],
                tight=True,
            ),
            padding=ft.padding.only(top=SPACING['sm']),
        ),
        actions=[
            ft.TextButton('Cancelar', on_click=lambda _: close_dlg()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_dlg(event: dict | None = None) -> None:
        form_error.visible = False
        if event is None:
            editing_event_id[0] = None
            title_field.value = ''
            event_dt_state['dt'] = None
            sync_date_display()
            description_field.value = ''
            save_button.text = 'Criar evento'
            event_dlg.title = ft.Text('Novo evento')
        else:
            editing_event_id[0] = event['id']
            title_field.value = event.get('title', '')
            event_dt_state['dt'] = _parse_api_datetime(event.get('date', ''))
            sync_date_display()
            description_field.value = event.get('description', '')
            save_button.text = 'Salvar alterações'
            event_dlg.title = ft.Text('Editar evento')
        page.dialog = event_dlg
        event_dlg.open = True
        page.update()

    def close_dlg() -> None:
        event_dlg.open = False
        page.update()

    # --- Save ---
    async def handle_save(_: ft.ControlEvent):
        form_error.visible = False
        save_button.disabled = True
        page.update()

        title = (title_field.value or '').strip()
        dt = event_dt_state['dt']
        description = (description_field.value or '').strip()

        if not title:
            form_error.value = 'Título é obrigatório.'
            form_error.visible = True
            save_button.disabled = False
            page.update()
            return

        if not dt:
            form_error.value = 'Informe a data e o horário.'
            form_error.visible = True
            save_button.disabled = False
            page.update()
            return

        payload = {'title': title, 'date': dt.isoformat(timespec='seconds'), 'description': description}
        client = APIClient(state, page)
        try:
            if editing_event_id[0] is None:
                await create_event(client, slug, payload)
                success_msg.value = 'Evento criado.'
            else:
                await update_event(client, slug, editing_event_id[0], payload)
                success_msg.value = 'Evento atualizado.'
            success_msg.visible = True
            close_dlg()
            await load_events_data()
        except APIError as ex:
            form_error.value = ex.message
            form_error.visible = True
        except Exception:
            form_error.value = 'Erro ao salvar evento.'
            form_error.visible = True
        finally:
            save_button.disabled = False
            page.update()

    save_button.on_click = handle_save

    # --- Load ---
    async def load_events_data():
        if not await require_group_admin(page, state, slug):
            loading.visible = False
            page.update()
            return
        loading.visible = True
        events_list.controls.clear()
        page.update()
        client = APIClient(state, page)
        try:
            events = await list_events(client, slug, ordering='-date')
            if not events:
                events_list.controls.append(
                    EmptyState('Nenhum evento encontrado.', icon=ft.icons.EVENT_BUSY)
                )
            else:
                for event in events:
                    events_list.controls.append(_build_event_row(event))
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao carregar eventos.'
            error_msg.visible = True
        finally:
            loading.visible = False
            page.update()

    # --- Event row ---
    def _build_event_row(event: dict) -> ft.Container:
        async def on_delete(_: ft.ControlEvent):
            error_msg.visible = False
            success_msg.visible = False
            client = APIClient(state, page)
            try:
                await delete_event(client, slug, event['id'])
                success_msg.value = 'Evento removido.'
                success_msg.visible = True
                await load_events_data()
            except APIError as ex:
                error_msg.value = ex.message
                error_msg.visible = True
            except Exception:
                error_msg.value = 'Erro ao remover evento.'
                error_msg.visible = True
            page.update()

        def go_to_members(_: ft.ControlEvent):
            page.go(f"/groups/{slug}/events/{event['id']}/members")

        def go_to_songs(_: ft.ControlEvent):
            page.go(f"/groups/{slug}/events/{event['id']}/songs")

        inner = ft.Column(
            [
                ft.Text(event['title'], weight=ft.FontWeight.W_600),
                ft.Text(
                    format_event_date(event.get('date', '')),
                    size=FONT_SIZES['body'],
                    color=COLORS['secondary'],
                ),
                ft.Text(event.get('description') or 'Sem descrição', size=FONT_SIZES['body']),
                ft.Row(
                    [
                        ft.OutlinedButton('Membros', icon=ft.icons.PEOPLE_OUTLINE, on_click=go_to_members),
                        ft.OutlinedButton('Setlist', icon=ft.icons.QUEUE_MUSIC_ROUNDED, on_click=go_to_songs),
                        ft.FilledTonalButton('Editar', icon=ft.icons.EDIT_OUTLINED, on_click=lambda _, ev=event: open_dlg(ev)),
                        ft.TextButton('Excluir', on_click=on_delete),
                    ],
                    wrap=True,
                    spacing=SPACING['sm'],
                ),
            ],
            spacing=SPACING['sm'],
        )
        return SurfaceCard(inner, padding=SPACING['md'])

    page.run_task(load_events_data)

    new_event_btn = ft.FilledTonalButton(
        '+ Novo evento',
        icon=ft.icons.ADD_ROUNDED,
        on_click=lambda _: open_dlg(),
    )

    content = ft.Column(
        [
            error_msg,
            success_msg,
            SectionTitle('Eventos do grupo', trailing=new_event_btn),
            loading,
            SurfaceCard(events_list, padding=SPACING['sm'], expand=1),
        ],
        spacing=SPACING['md'],
        expand=True,
    )

    def go_back(_: ft.ControlEvent):
        page.go(f'/groups/{slug}')

    return ft.View(
        f'/groups/{slug}/events',
        [
            ft.AppBar(
                title=ft.Text('Gerenciar eventos'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
