"""Instrumentos alinhados ao backend (apps.common.instruments). slug -> ícone Material."""

import flet as ft

# Lista ordenada para UI (slug, rótulo, ícone)
INSTRUMENT_OPTIONS: list[tuple[str, str, str]] = [
    ('vocalist', 'Vocal', ft.icons.MIC_ROUNDED),
    ('guitar', 'Violão / guitarra', ft.icons.MUSIC_NOTE_ROUNDED),
    ('bass', 'Baixo', ft.icons.QUEUE_MUSIC_ROUNDED),
    ('keyboard', 'Teclado', ft.icons.PIANO_ROUNDED),
    ('drums', 'Bateria', ft.icons.ALBUM_ROUNDED),
    ('other', 'Outro', ft.icons.MUSIC_OFF_ROUNDED),
]

INSTRUMENT_LABELS: dict[str, str] = {s: label for s, label, _ in INSTRUMENT_OPTIONS}


def format_instruments_slugs(slugs: list | None) -> str:
    if not slugs:
        return '—'
    return ' · '.join(INSTRUMENT_LABELS.get(s, s) for s in slugs)
