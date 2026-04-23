# Escala Louvor

Worship band scheduling system — Django REST API + Flet UI.

## Setup

### Prerequisites

- Python 3.10+
- Poetry 2.2+

### Backend

```bash
cd backend
poetry install
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
poetry run flet run --web frontend/main.py
```

UI: http://localhost:8000

### Testing

```bash
cd backend
poetry run python manage.py test --verbosity=2
```

## Project Structure

```
escala-louvor/
├── backend/
│   ├── escala/              # Django project settings
│   ├── apps/
│   │   ├── accounts/        # User auth (JWT)
│   │   ├── groups/          # Group management + permissions
│   │   └── events/          # Events, songs, participation
│   ├── pyproject.toml       # Poetry dependencies
│   ├── poetry.lock          # Lock file (commit this)
│   ├── manage.py
│   └── .env.example
│
├── frontend/
│   ├── main.py              # Flet app entry point
│   ├── api/                 # API client
│   ├── state/               # App state management
│   ├── pages/               # UI pages
│   ├── pyproject.toml
│   └── poetry.lock
│
├── .claude/
│   ├── skills/              # Claude Code skills
│   └── settings.json
├── CLAUDE.md                # Project guidelines
└── .gitignore
```

## Architecture

- **SOLID Principles**: SRP (models/views/serializers separated), DI (permission classes)
- **Clean Architecture**: Layered (models → views → serializers), testable
- **OWASP**: A01 (Access Control), A02 (Crypto), A05 (Misconfiguration), etc.

See `CLAUDE.md` for detailed standards.

## Development

### Add Dependencies

```bash
cd backend
poetry add <package>
poetry add <package> --group dev
```

### Run with Poetry Shell

```bash
poetry shell    # activate virtual environment
python manage.py runserver
exit            # deactivate
```

Or run directly:

```bash
poetry run python manage.py runserver
poetry run pytest
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
SECRET_KEY=<your-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Production: see `.env.example` for PostgreSQL settings.

## Resources

- [Django Docs](https://docs.djangoproject.com/)
- [DRF](https://www.django-rest-framework.org/)
- [Flet](https://flet.io/)
- [Poetry](https://python-poetry.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
