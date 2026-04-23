"""
Referência: CircleAvatar com foto URL (Flet 0.21).
Parâmetro: foreground_image_url (não confundir com nomes de outras versões).
"""
import flet as ft

avatar_com_foto = ft.CircleAvatar(
    radius=18,
    foreground_image_url="https://example.com/photo.jpg",
)

avatar_iniciais = ft.CircleAvatar(
    radius=18,
    bgcolor=ft.colors.SECONDARY_CONTAINER,
    color=ft.colors.ON_SECONDARY_CONTAINER,
    content=ft.Text("AB", size=12, weight=ft.FontWeight.W_600),
)
