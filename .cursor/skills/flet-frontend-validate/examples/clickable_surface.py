"""
Referência: em Flet 0.21 ft.InkWell pode não existir.
Use GestureDetector + Tooltip para ripple/tooltip equivalentes ao Material.
"""
import flet as ft


def build_chip(page: ft.Page) -> ft.Control:
    inner = ft.Row(
        [ft.Icon(ft.icons.PERSON_ROUNDED), ft.Text("Perfil")],
        tight=True,
    )

    def on_tap(_):
        page.go("/profile")

    return ft.Tooltip(
        message="Abrir perfil",
        content=ft.GestureDetector(
            content=ft.Container(content=inner, padding=8),
            on_tap=on_tap,
            mouse_cursor=ft.MouseCursor.CLICK,
        ),
    )
