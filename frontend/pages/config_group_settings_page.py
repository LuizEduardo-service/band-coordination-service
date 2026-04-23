import flet as ft
from api.client import APIClient, APIError
from api.groups import list_groups, get_group, update_group
from authz import require_group_admin
from state.app_state import AppState
from components.styled import FormField, PrimaryButton, ErrorText, PageContainer, SurfaceCard, EmptyState, SectionTitle
from components.app_bar_user import app_bar_user_row
from theme import COLORS, FONT_SIZES, SPACING, CARD_ELEVATION, RADIUS_CARD


def build_config_group_settings_page(page: ft.Page, state: AppState) -> ft.View:
    groups_list = ft.Column(spacing=SPACING['md'], expand=True, scroll=ft.ScrollMode.AUTO)
    loading = ft.ProgressRing(visible=True)
    error_msg = ErrorText()
    success_msg = ft.Text('', color=COLORS['success'], visible=False)

    selected_group_slug: str | None = None

    name_field = FormField(label='Nome do Grupo')
    description_field = FormField(label='Descrição (opcional)')
    slug_field = FormField(label='Slug (opcional)')
    save_button = PrimaryButton('Salvar alterações')
    save_button.disabled = True

    async def load_group_cards() -> None:
        nonlocal selected_group_slug
        loading.visible = True
        error_msg.visible = False
        groups_list.controls.clear()
        page.update()

        client = APIClient(state, page)
        try:
            groups = await list_groups(client)
            admin_groups = [g for g in groups if g.get('my_role') == 'admin']
            if not admin_groups:
                groups_list.controls.append(
                    EmptyState(
                        'Somente administradores de grupo podem alterar configurações. '
                        'Você não é admin de nenhum grupo.',
                        icon=ft.icons.LOCK_OUTLINE,
                    )
                )
            else:
                for group in admin_groups:
                    groups_list.controls.append(_build_group_card(group))
                if selected_group_slug is None and admin_groups:
                    await load_group_details(admin_groups[0]['slug'])
        except APIError as ex:
            error_msg.value = ex.detail
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao carregar grupos.'
            error_msg.visible = True
        finally:
            loading.visible = False
            page.update()

    async def load_group_details(slug: str) -> None:
        nonlocal selected_group_slug
        success_msg.visible = False
        error_msg.visible = False
        save_button.disabled = True
        page.update()

        client = APIClient(state, page)
        if not await require_group_admin(page, state, slug):
            save_button.disabled = True
            page.update()
            return
        try:
            group = await get_group(client, slug)
            selected_group_slug = group['slug']
            name_field.value = group.get('name', '')
            description_field.value = group.get('description', '')
            slug_field.value = group.get('slug', '')
            save_button.disabled = False
        except APIError as ex:
            error_msg.value = ex.detail
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao carregar detalhes do grupo.'
            error_msg.visible = True
        page.update()

    def _build_group_card(group: dict) -> ft.Card:
        def on_select(_: ft.ControlEvent) -> None:
            page.run_task(load_group_details, group['slug'])

        configure_btn = PrimaryButton('Configurar', width=None)
        configure_btn.on_click = on_select

        inner = ft.Column(
            [
                ft.Text(group['name'], weight=ft.FontWeight.W_600),
                ft.Text(
                    group.get('description', 'Sem descrição'),
                    color=COLORS['secondary'],
                    size=FONT_SIZES['body'],
                ),
                ft.Text(f"Slug: {group['slug']}", size=FONT_SIZES['body'], color=COLORS['secondary']),
                ft.Row(
                    [configure_btn],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=SPACING['sm'],
        )
        return ft.Card(
            elevation=CARD_ELEVATION,
            content=ft.Container(content=inner, padding=SPACING['md'], border_radius=RADIUS_CARD),
        )

    async def handle_save(_: ft.ControlEvent) -> None:
        nonlocal selected_group_slug
        error_msg.visible = False
        success_msg.visible = False
        save_button.disabled = True
        page.update()

        if not selected_group_slug:
            error_msg.value = 'Selecione um grupo para configurar.'
            error_msg.visible = True
            save_button.disabled = False
            page.update()
            return

        name = (name_field.value or '').strip()
        description = (description_field.value or '').strip()
        slug = (slug_field.value or '').strip()

        if not name:
            error_msg.value = 'Nome do grupo é obrigatório.'
            error_msg.visible = True
            save_button.disabled = False
            page.update()
            return

        payload = {'name': name, 'description': description}
        if slug:
            payload['slug'] = slug

        client = APIClient(state, page)
        try:
            updated_group = await update_group(client, selected_group_slug, payload)
            old_slug = selected_group_slug
            selected_group_slug = updated_group['slug']

            name_field.value = updated_group.get('name', '')
            description_field.value = updated_group.get('description', '')
            slug_field.value = updated_group.get('slug', '')

            if state.current_group and state.current_group.get('slug') == old_slug:
                state.current_group = updated_group

            success_msg.value = 'Configurações do grupo atualizadas com sucesso.'
            success_msg.visible = True
            await load_group_cards()
        except APIError as ex:
            error_msg.value = ex.detail
            error_msg.visible = True
        except Exception:
            error_msg.value = 'Erro ao atualizar grupo.'
            error_msg.visible = True
        finally:
            save_button.disabled = False
            page.update()

    save_button.on_click = handle_save
    page.run_task(load_group_cards)

    list_panel = SurfaceCard(
        ft.Column(
            [
                ft.Text('Seus grupos', weight=ft.FontWeight.W_600),
                loading,
                groups_list,
            ],
            spacing=SPACING['md'],
            expand=True,
        ),
        padding=SPACING['md'],
        expand=1,
    )

    edit_panel = SurfaceCard(
        ft.Column(
            [
                ft.Text('Editar grupo selecionado', weight=ft.FontWeight.W_600),
                name_field,
                description_field,
                slug_field,
                save_button,
            ],
            spacing=SPACING['md'],
        ),
        padding=SPACING['md'],
        expand=1,
    )

    content = ft.Column(
        [
            SectionTitle('Configurações de grupo'),
            error_msg,
            success_msg,
            ft.Row(
                [list_panel, edit_panel],
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=SPACING['md'],
            ),
        ],
        spacing=SPACING['md'],
        expand=True,
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
