import flet as ft
from api.client import APIClient, APIError
from api.auth import get_me, patch_me, upload_me_photo
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, PageContainer, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, RADIUS_FIELD
from instrument_icons import INSTRUMENT_OPTIONS


def build_profile_page(page: ft.Page, state: AppState) -> ft.View:
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)

    phone_field = FormField(label='Telefone', width=None)
    bio_field = ft.TextField(
        label='Sobre mim',
        hint_text='Conte um pouco sobre você e sua experiência com louvor',
        multiline=True,
        min_lines=3,
        max_lines=6,
        filled=True,
        border_radius=RADIUS_FIELD,
    )

    selected_slugs: set[str] = set()
    chip_controls: list[ft.Chip] = []

    photo_preview = ft.Container(
        width=120,
        height=120,
        border_radius=60,
        bgcolor=COLORS['surface_container'],
        alignment=ft.alignment.center,
        content=ft.Icon(ft.icons.PERSON_ROUNDED, size=56, color=COLORS['secondary']),
    )

    def refresh_chips_selection() -> None:
        for chip in chip_controls:
            slug = chip.data
            chip.selected = slug in selected_slugs

    def sync_form_from_state() -> None:
        u = state.user or {}
        phone_field.value = u.get('phone') or ''
        bio_field.value = u.get('bio') or ''
        selected_slugs.clear()
        for s in u.get('instruments') or []:
            selected_slugs.add(s)
        refresh_chips_selection()
        url = u.get('photo')
        if url:
            photo_preview.content = ft.Image(src=url, width=120, height=120, fit=ft.ImageFit.COVER)
            photo_preview.border_radius = 60
        else:
            photo_preview.content = ft.Icon(ft.icons.PERSON_ROUNDED, size=56, color=COLORS['secondary'])

    def on_chip_select(e: ft.ControlEvent) -> None:
        chip = e.control
        slug = chip.data
        if slug in selected_slugs:
            selected_slugs.remove(slug)
            chip.selected = False
        else:
            selected_slugs.add(slug)
            chip.selected = True
        page.update()

    for slug, label, icon in INSTRUMENT_OPTIONS:
        chip = ft.Chip(
            label=ft.Text(label),
            leading=ft.Icon(icon, size=18),
            selected=False,
            data=slug,
            on_select=on_chip_select,
            show_checkmark=True,
        )
        chip_controls.append(chip)

    sync_form_from_state()

    async def save_profile(_: ft.ControlEvent) -> None:
        error_msg.visible = False
        success_msg.visible = False
        page.update()
        client = APIClient(state, page)
        try:
            payload = {
                'phone': (phone_field.value or '').strip(),
                'bio': (bio_field.value or '').strip(),
                'instruments': sorted(selected_slugs),
            }
            await patch_me(client, payload)
            me = await get_me(client)
            state.user = me
            state.save(page)
            sync_form_from_state()
            success_msg.value = 'Perfil salvo.'
            success_msg.visible = True
        except APIError as ex:
            error_msg.value = str(ex.detail)
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao salvar perfil.'
            error_msg.visible = True
        page.update()

    async def on_photo_picked(e: ft.FilePickerResultEvent) -> None:
        if not e.files:
            return
        f = e.files[0]
        path = f.path
        name = f.name or 'foto.jpg'
        if not path:
            error_msg.value = 'Não foi possível ler o arquivo (ambiente web pode exigir outro fluxo).'
            error_msg.visible = True
            page.update()
            return
        try:
            with open(path, 'rb') as fh:
                raw = fh.read()
        except OSError:
            error_msg.value = 'Não foi possível abrir a imagem.'
            error_msg.visible = True
            page.update()
            return
        error_msg.visible = False
        page.update()
        client = APIClient(state, page)
        try:
            me = await upload_me_photo(client, raw, name)
            state.user = me
            state.save(page)
            sync_form_from_state()
            success_msg.value = 'Foto atualizada.'
            success_msg.visible = True
        except APIError as ex:
            error_msg.value = str(ex.detail)
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao enviar foto.'
            error_msg.visible = True
        page.update()

    if state.profile_file_picker is None:
        state.profile_file_picker = ft.FilePicker()
        page.overlay.append(state.profile_file_picker)
    state.profile_file_picker.on_result = on_photo_picked

    def pick_photo(_: ft.ControlEvent) -> None:
        state.profile_file_picker.pick_files(
            dialog_title='Escolher foto',
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    chips_wrap = ft.Row(
        wrap=True,
        spacing=SPACING['sm'],
        run_spacing=SPACING['sm'],
        controls=chip_controls,
    )

    save_btn = PrimaryButton('Salvar perfil', width=None)
    save_btn.on_click = save_profile

    content = ft.Column(
        [
            SectionTitle('Meu perfil'),
            error_msg,
            success_msg,
            ft.Row(
                [
                    photo_preview,
                    ft.Column(
                        [
                            ft.OutlinedButton(
                                'Alterar foto',
                                icon=ft.icons.PHOTO_CAMERA_OUTLINED,
                                on_click=pick_photo,
                            ),
                            ft.Text(
                                'JPG, PNG ou WebP',
                                size=FONT_SIZES['body'],
                                color=COLORS['secondary'],
                            ),
                        ],
                        spacing=SPACING['xs'],
                        tight=True,
                    ),
                ],
                spacing=SPACING['lg'],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            phone_field,
            bio_field,
            SectionTitle('Instrumentos que você toca'),
            chips_wrap,
            save_btn,
        ],
        spacing=SPACING['md'],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def go_back(_: ft.ControlEvent) -> None:
        page.go('/dashboard')

    return ft.View(
        '/profile',
        [
            ft.AppBar(
                title=ft.Text('Perfil'),
                leading=ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, on_click=go_back),
                actions=[app_bar_user_row(page, state)],
            ),
            PageContainer(content),
        ],
    )
