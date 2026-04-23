"""
Referência: em Flet 0.21 não há ft.Wrap.
Use Row com wrap=True para fluxo que quebra linha (chips, botões).
"""
import flet as ft

# Em vez de: ft.Wrap(controls=[...])
row = ft.Row(
    controls=[
        ft.FilledButton("A"),
        ft.FilledButton("B"),
    ],
    wrap=True,
    spacing=8,
    run_spacing=8,
)
