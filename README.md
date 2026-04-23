# Escala Louvor

Worship band scheduling system — Django REST API + Flet UI.

## Stack

- **Backend**: Django 4.2 + DRF + SimpleJWT + PostgreSQL (SQLite in dev)
- **Frontend**: Flet + httpx
- **Auth**: JWT (access 15min / refresh 7 days)
- **Standards**: SOLID, Clean Architecture, OWASP Top 10

## Setup

### Prerequisites

- Python 3.10+
- Poetry 2.2+

### Backend

```bash
cd backend
poetry install
cp .env.example .env       # fill in SECRET_KEY etc.
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
poetry run python manage.py runserver
```

API: http://localhost:8000/api/v1/

Admin: http://localhost:8000/admin/

### Frontend

```bash
cd frontend
poetry install
poetry run flet run main.py
```

UI: http://localhost:8550 (default Flet port)

### Testing

```bash
cd backend
poetry run python manage.py test apps.accounts apps.events apps.invites --verbosity=2
```

## Project Structure

```
escala-louvor/
├── backend/
│   ├── escala/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py   # SQLite, DEBUG=True
│   │   │   └── production.py    # PostgreSQL, env secrets
│   │   └── urls.py
│   ├── apps/
│   │   ├── accounts/            # CustomUser, UserProfile, JWT auth
│   │   ├── common/
│   │   │   ├── instruments.py   # INSTRUMENT_CHOICES shared constant
│   │   │   └── mixins.py        # GroupScopedMixin (shared by all views)
│   │   ├── groups/              # Group, Membership, permissions
│   │   ├── events/              # Event, Song, EventMember, EventSong, SongSuggestion
│   │   └── invites/             # Invite (group + event)
│   ├── manage.py
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/
│   ├── main.py                  # Flet entry + routing
│   ├── api/
│   │   ├── client.py            # httpx wrapper, JWT auto-refresh
│   │   ├── auth.py
│   │   ├── groups.py
│   │   ├── events.py
│   │   ├── songs.py
│   │   ├── song_suggestions.py
│   │   └── invites.py
│   ├── components/
│   │   ├── styled.py            # Reusable Flet components
│   │   └── app_bar_user.py
│   ├── pages/                   # 15 UI pages
│   ├── state/
│   │   └── app_state.py         # Global AppState + session persistence
│   ├── utils/
│   │   └── date_utils.py        # format_event_date()
│   └── pyproject.toml
│
├── .claude/
│   ├── settings.json
│   ├── TEAM_AGENTS.md
│   └── skills/
├── .claudeignore
├── .gitignore
├── CLAUDE.md                    # Code standards + architecture
└── PRD.md                       # Product requirements
```

## Architecture

```
Entities    → Models (pure, minimal deps)
    ↑
Use Cases   → Views (orchestrate)
    ↑
Controllers → ViewSets (handle HTTP)
    ↑
Web         → Serializers, URLs, DRF
```

Access control: every resource scoped to a `Group`. All views use `GroupScopedMixin` + `IsGroupMember`/`IsGroupAdmin` permission classes.

See `CLAUDE.md` for detailed standards (SOLID, Clean Architecture, OWASP).

## Environment Variables

```bash
cp backend/.env.example backend/.env
```

Key variables:

| Variable | Dev | Production |
|----------|-----|------------|
| `SECRET_KEY` | any string | strong random |
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `*` | `yourdomain.com` |
| `DB_*` | — (SQLite) | PostgreSQL credentials |

## Dependencies

**Backend** (`python ^3.10`):
`django`, `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers`, `python-decouple`, `psycopg2-binary`, `pillow`

**Frontend** (`python ^3.10`):
`flet`, `httpx`

## Resources

- [Django Docs](https://docs.djangoproject.com/)
- [DRF](https://www.django-rest-framework.org/)
- [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Flet](https://flet.io/docs/)
- [Poetry](https://python-poetry.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
