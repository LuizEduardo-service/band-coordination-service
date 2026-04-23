import flet as ft
from theme import build_page_theme_dark, build_page_theme_light
from state.app_state import AppState
from pages.login_page import build_login_page
from pages.register_page import build_register_page
from pages.dashboard_page import build_dashboard_page
from pages.invites_page import build_invites_page
from pages.config_group_page import build_config_group_page
from pages.group_page import build_group_page
from pages.config_members_page import build_config_members_page
from pages.config_songs_page import build_config_songs_page
from pages.add_song_page import build_add_song_page
from pages.config_group_settings_page import build_config_group_settings_page
from pages.config_events_page import build_config_events_page
from pages.config_event_members_page import build_config_event_members_page
from pages.config_event_songs_page import build_config_event_songs_page
from pages.event_detail_page import build_event_detail_page
from pages.profile_page import build_profile_page


async def main(page: ft.Page) -> None:
    page.title = 'Escala Louvor'
    page.theme = build_page_theme_light()
    page.dark_theme = build_page_theme_dark()
    page.theme_mode = ft.ThemeMode.SYSTEM

    state = AppState()
    state.load(page)

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        route = page.route

        if not state.is_authenticated:
            if route == '/register':
                page.views.append(build_register_page(page, state))
            else:
                page.views.append(build_login_page(page, state))
        elif route in ('/login', '/register'):
            page.go('/dashboard')
            return
        elif route == '/dashboard':
            page.views.append(build_dashboard_page(page, state))
        elif route == '/invites':
            page.views.append(build_invites_page(page, state))
        elif route == '/profile':
            page.views.append(build_profile_page(page, state))
        elif route == '/config/groups/create':
            page.views.append(build_config_group_page(page, state))
        elif route == '/config/groups/settings':
            page.views.append(build_config_group_settings_page(page, state))
        elif route.startswith('/groups/') and '/events/' in route and route.endswith('/members'):
            parts = route.split('/')
            if len(parts) >= 6 and parts[4].isdigit():
                slug = parts[2]
                event_id = int(parts[4])
                page.views.append(build_config_event_members_page(page, state, slug, event_id))
            else:
                page.go('/dashboard')
        elif route.startswith('/groups/') and '/events/' in route and route.endswith('/songs'):
            parts = route.split('/')
            if len(parts) >= 6 and parts[4].isdigit():
                slug = parts[2]
                event_id = int(parts[4])
                page.views.append(build_config_event_songs_page(page, state, slug, event_id))
            else:
                page.go('/dashboard')
        elif route.startswith('/groups/') and '/events/' in route:
            path_parts = route.strip('/').split('/')
            if len(path_parts) == 4 and path_parts[2] == 'events' and path_parts[3].isdigit():
                slug = path_parts[1]
                event_id = int(path_parts[3])
                page.views.append(build_event_detail_page(page, state, slug, event_id))
            else:
                page.go('/dashboard')
        elif route.startswith('/groups/') and route.endswith('/events'):
            parts = route.split('/')
            if len(parts) >= 4:
                slug = parts[2]
                page.views.append(build_config_events_page(page, state, slug))
            else:
                page.go('/dashboard')
        elif '/members' in route:
            parts = route.split('/')
            if len(parts) >= 3:
                slug = parts[2]
                page.views.append(build_config_members_page(page, state, slug))
            else:
                page.go('/dashboard')
        elif route.endswith('/songs/new'):
            parts = route.split('/')
            if len(parts) >= 3:
                slug = parts[2]
                page.views.append(build_add_song_page(page, state, slug))
            else:
                page.go('/dashboard')
        elif '/songs' in route:
            parts = route.split('/')
            if len(parts) >= 3:
                slug = parts[2]
                page.views.append(build_config_songs_page(page, state, slug))
            else:
                page.go('/dashboard')
        elif route.startswith('/groups/'):
            parts = route.split('/')
            if len(parts) >= 3:
                slug = parts[2]
                page.views.append(build_group_page(page, state, slug))
            else:
                page.go('/dashboard')
        else:
            page.go('/dashboard' if state.is_authenticated else '/login')

        page.update()

    def view_pop(e: ft.ViewPopEvent) -> None:
        if page.views:
            page.views.pop()
        if page.views:
            top = page.views[-1]
            page.go(top.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    if state.is_authenticated:
        page.go('/dashboard')
    else:
        page.go('/login')


ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)
