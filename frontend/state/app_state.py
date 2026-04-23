from dataclasses import dataclass, field
from typing import Any
import flet as ft


@dataclass
class AppState:
    token: str | None = None
    refresh_token: str | None = None
    user: dict | None = None
    current_group: dict | None = None
    profile_file_picker: Any = field(default=None, repr=False)

    def load(self, page: ft.Page) -> None:
        self.token = page.session.get('token')
        self.refresh_token = page.session.get('refresh_token')
        self.user = page.session.get('user')

    def save(self, page: ft.Page) -> None:
        if self.token:
            page.session.set('token', self.token)
        if self.refresh_token:
            page.session.set('refresh_token', self.refresh_token)
        if self.user:
            page.session.set('user', self.user)

    def clear(self, page: ft.Page) -> None:
        self.token = None
        self.refresh_token = None
        self.user = None
        self.current_group = None
        try:
            page.session.remove('token')
        except Exception:
            pass
        try:
            page.session.remove('refresh_token')
        except Exception:
            pass
        try:
            page.session.remove('user')
        except Exception:
            pass

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None
