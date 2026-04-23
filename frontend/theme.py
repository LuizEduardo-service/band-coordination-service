import flet as ft

# Cor de destaque Material 3 (tom índigo — ajuste único para identidade)
ACCENT_SEED = ft.colors.INDIGO_700

# Raio e elevação (tokens de layout)
RADIUS_FIELD = 12
RADIUS_CARD = 16
RADIUS_SURFACE = 16
CARD_ELEVATION = 1.5

# Palette legada + tokens alinhados ao M3 (funciona com e sem Theme global)
COLORS = {
    'primary': ft.colors.PRIMARY,
    'error': ft.colors.ERROR,
    'secondary': ft.colors.ON_SURFACE_VARIANT,
    'background': ft.colors.SURFACE,
    'surface_container': ft.colors.SURFACE_VARIANT,
    'outline': ft.colors.OUTLINE_VARIANT,
    'transparent': ft.colors.TRANSPARENT,
    'success': ft.colors.TERTIARY,
}

SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 24,
    'xl': 40,
}

FONT_SIZES = {
    'title': 28,
    'subtitle': 18,
    'label': 14,
    'body': 12,
}


def outline_border(width: float = 1) -> ft.Border:
    return ft.border.all(width, COLORS['outline'])


def build_page_theme_light() -> ft.Theme:
    transitions = ft.PageTransitionsTheme(
        android=ft.PageTransitionTheme.FADE_UPWARDS,
        ios=ft.PageTransitionTheme.CUPERTINO,
    )
    return ft.Theme(
        use_material3=True,
        color_scheme_seed=ACCENT_SEED,
        page_transitions=transitions,
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
    )


def build_page_theme_dark() -> ft.Theme:
    transitions = ft.PageTransitionsTheme(
        android=ft.PageTransitionTheme.FADE_UPWARDS,
        ios=ft.PageTransitionTheme.CUPERTINO,
    )
    dark_scheme = ft.ColorScheme(
        primary=ft.colors.INDIGO_200,
        on_primary=ft.colors.INDIGO_900,
        primary_container=ft.colors.INDIGO_700,
        on_primary_container=ft.colors.INDIGO_100,
        secondary=ft.colors.BLUE_GREY_200,
        on_secondary=ft.colors.BLUE_GREY_900,
        tertiary=ft.colors.TEAL_200,
        on_tertiary=ft.colors.TEAL_900,
        error=ft.colors.RED_300,
        on_error=ft.colors.RED_900,
        surface=ft.colors.GREY_900,
        on_surface=ft.colors.GREY_100,
        surface_variant=ft.colors.GREY_800,
        on_surface_variant=ft.colors.GREY_400,
        outline=ft.colors.GREY_600,
        outline_variant=ft.colors.GREY_700,
    )
    return ft.Theme(
        use_material3=True,
        color_scheme=dark_scheme,
        page_transitions=transitions,
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
    )
