import flet as ft
from api.client import APIClient, APIError
from api.groups import list_groups, update_group, delete_group, upload_group_avatar
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, DangerButton, ErrorText, PageContainer, EmptyState, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, CARD_ELEVATION, RADIUS_CARD, ICON_SIZES


_AVATAR_SIZE = 72
_AVATAR_RADIUS = _AVATAR_SIZE // 2


def build_config_group_settings_page(page: ft.Page, state: AppState) -> ft.View:
    groups_list = ft.Column(spacing=SPACING['sm'])
    loading = ft.ProgressRing(visible=True)
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)

    editing: dict = {}

    # --- Avatar preview ---
    avatar_preview = ft.Container(
        width=_AVATAR_SIZE,
        height=_AVATAR_SIZE,
        border_radius=_AVATAR_RADIUS,
        bgcolor=COLORS['surface_container'],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Icon(ft.icons.GROUP_WORK_OUTLINED, size=ICON_SIZES['lg'], color=COLORS['secondary']),
    )

    # --- FilePicker ---
    async def handle_avatar_upload(f) -> None:
        slug = editing.get('slug')
        if not slug:
            return
        try:
            raw = open(f.path, 'rb').read()
            avatar_preview.content = ft.ProgressRing(visible=True)
            page.update()
            client = APIClient(state, page)
            updated = await upload_group_avatar(client, slug, raw, f.name)
            avatar_url = updated.get('avatar_url')
            if avatar_url:
                avatar_preview.content = ft.Image(
                    src=avatar_url,
                    width=_AVATAR_SIZE,
                    height=_AVATAR_SIZE,
                    fit=ft.ImageFit.COVER,
                )
            else:
                avatar_preview.content = ft.Icon(ft.icons.GROUP_WORK_OUTLINED, size=ICON_SIZES['lg'], color=COLORS['secondary'])
            success_msg.value = 'Foto enviada com sucesso.'
            success_msg.visible = True
        except Exception as ex:
            error_msg.value = f'Erro ao enviar foto: {str(ex)}'
            error_msg.visible = True
            avatar_preview.content = ft.Icon(ft.icons.GROUP_WORK_OUTLINED, size=ICON_SIZES['lg'], color=COLORS['secondary'])
        page.update()

    def on_file_picked(e: ft.FilePickerResultEvent) -> None:
        if e.files:
            page.run_task(handle_avatar_upload, e.files[0])

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def pick_avatar(_: ft.ControlEvent) -> None:
        file_picker.pick_files(
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
            allow_multiple=False,
        )

    # --- Form fields ---
    name_field = FormField(label='Nome do grupo')
    description_field = FormField(label='Descrição (opcional)')
    form_error = ErrorText()
    save_btn = PrimaryButton('Salvar alterações', expand=False)

    # --- Dialog helpers ---
    def _open_dialog(dlg: ft.AlertDialog) -> None:
        page.dialog = dlg
        dlg.open = True
        page.update()

    def _close_dialog(dlg: ft.AlertDialog) -> None:
        dlg.open = False
        page.update()

    # --- Deactivate dialog ---
    deactivate_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text('Desativar grupo?'),
        content=ft.Text('O grupo não aparecerá mais na listagem dos membros. Pode reativar pelo painel admin.'),
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # --- Delete dialog ---
    delete_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text('Excluir grupo?'),
        content=ft.Text('Ação irreversível. Todos os eventos, músicas e membros serão excluídos permanentemente.'),
        actions_alignment=ft.MainAxisAlignment.END,
    )

    async def handle_deactivate(_: ft.ControlEvent) -> None:
        slug = editing.get('slug')
        if not slug:
            return
        _close_dialog(deactivate_dlg)
        client = APIClient(state, page)
        try:
            await update_group(client, slug, {'is_active': False})
            success_msg.value = 'Grupo desativado.'
            success_msg.visible = True
            editing.clear()
            await _load_groups()
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
            page.update()

    async def handle_delete(_: ft.ControlEvent) -> None:
        slug = editing.get('slug')
        if not slug:
            return
        _close_dialog(delete_dlg)
        client = APIClient(state, page)
        try:
            await delete_group(client, slug)
            success_msg.value = 'Grupo excluído.'
            success_msg.visible = True
            editing.clear()
            await _load_groups()
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
            page.update()

    deactivate_dlg.actions = [
        ft.TextButton('Cancelar', on_click=lambda _: _close_dialog(deactivate_dlg)),
        ft.FilledTonalButton('Desativar', on_click=handle_deactivate),
    ]
    _danger_delete_btn = DangerButton('Excluir')
    _danger_delete_btn.on_click = handle_delete
    delete_dlg.actions = [
        ft.TextButton('Cancelar', on_click=lambda _: _close_dialog(delete_dlg)),
        _danger_delete_btn,
    ]

    # --- Edit dialog ---
    edit_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text('Editar grupo'),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    avatar_preview,
                                    ft.OutlinedButton(
                                        'Alterar foto',
                                        icon=ft.icons.PHOTO_CAMERA_OUTLINED,
                                        on_click=pick_avatar,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=SPACING['xs'],
                                tight=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    form_error,
                    name_field,
                    description_field,
                ],
                spacing=SPACING['sm'],
                tight=True,
            ),
            padding=ft.padding.only(top=SPACING['sm']),
        ),
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def close_edit_dlg() -> None:
        edit_dlg.open = False
        page.update()

    async def handle_save(_: ft.ControlEvent) -> None:
        form_error.visible = False
        slug = editing.get('slug')
        if not slug:
            return

        name = (name_field.value or '').strip()
        description = (description_field.value or '').strip()

        if not name:
            form_error.value = 'Nome é obrigatório.'
            form_error.visible = True
            page.update()
            return

        save_btn.disabled = True
        page.update()
        client = APIClient(state, page)
        try:
            updated = await update_group(client, slug, {'name': name, 'description': description})

            if state.current_group and state.current_group.get('slug') == slug:
                state.current_group = updated
            editing['slug'] = updated['slug']
            close_edit_dlg()
            success_msg.value = 'Grupo atualizado.'
            success_msg.visible = True
            await _load_groups()
        except APIError as ex:
            form_error.value = ex.message
            form_error.visible = True
        except Exception:
            form_error.value = 'Erro ao salvar.'
            form_error.visible = True
        finally:
            save_btn.disabled = False
            page.update()

    save_btn.on_click = handle_save

    edit_dlg.actions = [
        ft.TextButton('Cancelar', on_click=lambda _: close_edit_dlg()),
        ft.TextButton(
            'Excluir',
            icon=ft.icons.DELETE_OUTLINE,
            style=ft.ButtonStyle(color=COLORS['error']),
            on_click=lambda _: (close_edit_dlg(), _open_dialog(delete_dlg)),
        ),
        ft.FilledTonalButton(
            'Desativar',
            icon=ft.icons.VISIBILITY_OFF_OUTLINED,
            on_click=lambda _: (close_edit_dlg(), _open_dialog(deactivate_dlg)),
        ),
        save_btn,
    ]

    # --- Load groups ---
    async def _load_groups() -> None:
        loading.visible = True
        error_msg.visible = False
        success_msg.visible = False
        groups_list.controls.clear()
        page.update()

        client = APIClient(state, page)
        try:
            groups = await list_groups(client)
            admin_groups = [g for g in groups if g.get('my_role') == 'admin']
            if not admin_groups:
                groups_list.controls.append(
                    EmptyState('Você não é administrador de nenhum grupo.', icon=ft.icons.LOCK_OUTLINE)
                )
            else:
                for group in admin_groups:
                    groups_list.controls.append(_build_group_tile(group))
        except APIError as ex:
            error_msg.value = ex.message
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao carregar grupos.'
            error_msg.visible = True
        finally:
            loading.visible = False
            page.update()

    def _open_edit_for(group: dict) -> None:
        editing['slug'] = group['slug']
        avatar_bytes[0] = None
        form_error.visible = False
        name_field.value = group.get('name', '')
        description_field.value = group.get('description', '')

        avatar_url = group.get('avatar_url')
        if avatar_url:
            avatar_preview.content = ft.Image(
                src=avatar_url,
                width=_AVATAR_SIZE,
                height=_AVATAR_SIZE,
                fit=ft.ImageFit.COVER,
            )
        else:
            avatar_preview.content = ft.Icon(
                ft.icons.GROUP_WORK_OUTLINED, size=ICON_SIZES['lg'], color=COLORS['secondary']
            )
        _open_dialog(edit_dlg)

    def _build_group_tile(group: dict) -> ft.Card:
        avatar_url = group.get('avatar_url')
        if avatar_url:
            avatar_widget = ft.Container(
                width=40,
                height=40,
                border_radius=20,
                bgcolor=COLORS['surface_container'],
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(src=avatar_url, width=40, height=40, fit=ft.ImageFit.COVER),
            )
        else:
            avatar_widget = ft.Container(
                width=40,
                height=40,
                border_radius=20,
                bgcolor=COLORS['surface_container'],
                content=ft.Icon(ft.icons.GROUP_WORK_OUTLINED, size=ICON_SIZES['sm'], color=COLORS['primary']),
                alignment=ft.alignment.center,
            )

        def on_tap(_: ft.ControlEvent) -> None:
            _open_edit_for(group)

        return ft.Card(
            elevation=CARD_ELEVATION,
            content=ft.Container(
                content=ft.ListTile(
                    leading=avatar_widget,
                    title=ft.Text(group['name'], weight=ft.FontWeight.W_600),
                    subtitle=ft.Text(
                        group.get('description') or group['slug'],
                        color=COLORS['secondary'],
                        size=FONT_SIZES['body'],
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    trailing=ft.Icon(ft.icons.CHEVRON_RIGHT_ROUNDED, color=COLORS['secondary']),
                    on_click=on_tap,
                ),
                border_radius=RADIUS_CARD,
            ),
        )

    page.run_task(_load_groups)

    content = ft.Column(
        [
            SectionTitle('Configurar grupos'),
            error_msg,
            success_msg,
            loading,
            groups_list,
        ],
        spacing=SPACING['md'],
        scroll=ft.ScrollMode.AUTO,
    )

    def go_back(_: ft.ControlEvent) -> None:
        page.go('/dashboard')

    return ft.View(
        '/config/groups/settings',
        [
            ft.AppBar(
                title=ft.Text('Configurar grupo'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
