from datetime import datetime


def format_event_date(value: str) -> str:
    if not value:
        return '-'
    try:
        normalized = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(normalized)
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return value
