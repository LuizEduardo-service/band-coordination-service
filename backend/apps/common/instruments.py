"""Slugs e labels de instrumentos — única fonte de verdade para models e DRF."""

from django.core.exceptions import ValidationError

INSTRUMENT_CHOICES = [
    ('vocalist', 'Vocal'),
    ('guitar', 'Violão/Guitarra'),
    ('bass', 'Baixo'),
    ('keyboard', 'Teclado'),
    ('drums', 'Bateria'),
    ('other', 'Outro'),
]

INSTRUMENT_SLUGS = frozenset(c[0] for c in INSTRUMENT_CHOICES)


def validate_instruments_list(value):
    if not isinstance(value, list):
        raise ValidationError('instruments deve ser uma lista.')
    seen = set()
    for item in value:
        if not isinstance(item, str):
            raise ValidationError('Cada instrumento deve ser texto (slug).')
        if item not in INSTRUMENT_SLUGS:
            raise ValidationError(f'Instrumento inválido: {item!r}.')
        if item in seen:
            raise ValidationError('Instrumentos duplicados não são permitidos.')
        seen.add(item)
    return value
