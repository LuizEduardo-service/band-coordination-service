"""Checagens de permissão no cliente (espelha papéis do backend)."""

import flet as ft

from api.client import APIClient, APIError
from state.app_state import AppState


async def require_group_admin(page: ft.Page, state: AppState, slug: str) -> bool:
    """Redireciona quem não é admin do grupo. Retorna True se puder continuar."""
    client = APIClient(state, page)
    try:
        group = await client.get(f'/groups/{slug}/')
    except APIError:
        page.go('/dashboard')
        return False
    if group.get('my_role') != 'admin':
        page.go(f'/groups/{slug}')
        return False
    return True
