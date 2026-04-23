# Escala Louvor — Project Guidelines

## Code Standards (Non-Negotiable)

**All code must follow SOLID, Clean Architecture, and OWASP principles.**

### SOLID Principles

- **Single Responsibility**: Models define schema + validation. Serializers transform data. Views orchestrate. Permissions gate access.
- **Open/Closed**: Extend via inheritance/composition, don't modify existing code.
- **Liskov Substitution**: Permissions subclasses work interchangeably. Serializers inherit properly.
- **Interface Segregation**: Small, focused ViewSets. Permissions are granular (e.g., `IsGroupAdmin` not `CanDoEverything`).
- **Dependency Inversion**: Depend on permission classes, not hardcoded role checks. Use DRF serializers generically.

### Clean Architecture Layers

```
Entities       → Models (pure, minimal dependencies)
    ↑
Use Cases      → Views (orchestrate, call models/serializers)
    ↑
Controllers    → ViewSets (handle HTTP)
    ↑
Web            → Serializers, URLs, DRF framework
```

**Rule**: Never let a lower layer depend on an upper layer. Models never import Views. Serializers don't do queries.

### OWASP Security

**A01 Broken Access Control**
- Every endpoint: check permission class (`IsGroupMember`, `IsGroupAdmin`)
- Derive group/user context from URL/request, never trust client input (`?group_id=X`)
- Test: unauthorized user trying to access resource → 403 or 404, not 200

**A02 Cryptographic Failures**
- Passwords: always `user.set_password()` → hashed with PBKDF2
- Tokens: JWT access 15min, refresh 7 days, rotation enabled
- Production: HTTPS only, env vars for all secrets

**A03 Injection**
- Django ORM protects SQL injection (use `.filter()`, not string concatenation)
- Flet inputs: validate before using in queries

**A05 Misconfiguration**
- `DEBUG=False` in production
- `ALLOWED_HOSTS` restrictive
- Secrets in `.env`, never committed
- CORS whitelist specific origins in prod

**A06 Vulnerable Components**
- Run `pip audit` before deployments
- Keep Django/DRF updated (minor patches, security releases)

---

## Project Structure

```
escala-louvor/
├── backend/
│   ├── escala/
│   │   ├── settings/
│   │   │   ├── base.py        # shared Django config
│   │   │   ├── development.py # SQLite, DEBUG=True
│   │   │   └── production.py  # PostgreSQL, secrets via env
│   │   └── urls.py
│   ├── apps/
│   │   ├── accounts/          # CustomUser, UserProfile, JWT auth
│   │   ├── groups/            # Group, Membership, custom permissions
│   │   ├── events/            # Event, Song, EventMember, EventSong, SongSuggestion
│   │   ├── invites/           # Invite (group + event invitations)
│   │   └── common/            # Shared utilities (instruments.py)
│   ├── manage.py
│   └── pyproject.toml
├── frontend/
│   ├── main.py                # Flet app entry + routing (15 pages)
│   ├── authz.py               # Authorization helpers
│   ├── theme.py               # Color/spacing tokens
│   ├── instrument_icons.py    # Instrument icon mappings
│   ├── api/
│   │   ├── client.py          # httpx wrapper, JWT token injection + auto-refresh
│   │   ├── auth.py            # /auth/* calls
│   │   ├── groups.py
│   │   ├── events.py
│   │   ├── songs.py
│   │   ├── song_suggestions.py
│   │   └── invites.py
│   ├── components/
│   │   ├── styled.py          # Reusable Flet UI components
│   │   └── app_bar_user.py    # User profile app bar
│   ├── state/
│   │   └── app_state.py       # Global AppState, page.session persistence
│   └── pages/                 # 15 Flet UI pages
│       ├── login_page.py
│       ├── register_page.py
│       ├── dashboard_page.py
│       ├── profile_page.py
│       ├── group_page.py
│       ├── config_group_page.py
│       ├── config_group_settings_page.py
│       ├── config_members_page.py
│       ├── config_events_page.py
│       ├── config_event_members_page.py
│       ├── config_event_songs_page.py
│       ├── config_songs_page.py
│       ├── event_detail_page.py
│       └── invites_page.py
├── .claude/
│   ├── settings.json          # Project-specific Claude config + hooks
│   ├── TEAM_AGENTS.md         # Multi-agent coordination (frontend/backend/security)
│   └── skills/
│       └── frontend-refactor/ # Frontend componentization skill
├── .cursor/
│   ├── rules/                 # Cursor editor agent rules
│   └── skills/                # Cursor-specific skills
├── PRD.md                     # Product requirements document
└── CLAUDE.md                  # This file
```

---

## Apps Overview

### `accounts/`
- **Models**: `CustomUser` (extends AbstractUser), `UserProfile` (phone, bio, photo, instruments JSONField)
- **Views**: register, me (GET/PATCH), me/photo (upload), change-password, user search
- **Deps**: `pillow` for profile photo handling

### `groups/`
- **Models**: `Group` (name, slug, description), `Membership` (user+group, role: admin|member, is_vocalist)
- **Permissions**: `IsGroupMember`, `IsGroupAdmin` (custom DRF permission classes)
- **Rule**: slug auto-generated from name; always lookup group by slug from URL

### `events/`
- **Models**: `Event`, `EventMember` (XOR: membership OR guest_user), `Song`, `EventSong` (setlist with order), `SongSuggestion` (pending|approved|rejected)
- **Key constraint**: `EventMember` must have exactly one of `membership` or `guest_user`
- **Filters**: events support `upcoming`, `date_from`, `date_to`, `ordering`

### `invites/`
- **Models**: `Invite` (kind: group|event, status: pending|accepted|declined)
- **Logic**: accept creates `Membership` (group invite) or `EventMember` (event invite) via `transaction.atomic`
- **Unique constraints**: one pending invite per (invitee, group) and (invitee, event)

### `common/`
- `instruments.py`: `INSTRUMENT_CHOICES` + `validate_instruments_list()` shared across apps

---

## Multi-Tenancy (Soft)

Every resource belongs to a `Group`. Access is gated by `Membership`:

```python
# ALWAYS filter by group
events = Event.objects.filter(group=group)  # NOT Event.objects.all()
songs = Song.objects.filter(group=group)     # ALWAYS

# In views:
group = Group.objects.get(slug=slug)  # from URL
check_membership(request.user, group)  # custom permission
```

No resource leaks across groups. An admin of Group A cannot see Group B's events.

---

## API Endpoints Reference

All endpoints prefixed with `/api/v1/`.

| Endpoint | Method | Auth | Notes |
|----------|--------|------|-------|
| `auth/login/` | POST | No | JWT obtain |
| `auth/refresh/` | POST | No | Refresh token |
| `auth/register/` | POST | No | Create user |
| `auth/me/` | GET/PATCH | Yes | Profile |
| `auth/me/photo/` | POST | Yes | Upload photo (multipart) |
| `auth/change-password/` | POST | Yes | Old + new password |
| `users/?search=` | GET | Yes | Min 2 chars, max 10 results |
| `groups/` | GET/POST | Yes | User's groups |
| `groups/<slug>/` | GET/PATCH | Yes | Admin for write |
| `groups/<slug>/members/` | GET/POST | Yes | Admin for POST |
| `groups/<slug>/members/<id>/` | PATCH/DELETE | Yes | Admin only |
| `groups/<slug>/invites/` | POST | Yes | Admin only |
| `groups/<slug>/songs/` | GET/POST | Yes | Song library |
| `groups/<slug>/songs/<id>/` | GET/PATCH/DELETE | Yes | Admin for write |
| `groups/<slug>/song-suggestions/` | POST | Yes | Any member |
| `groups/<slug>/events/` | GET/POST | Yes | Admin for POST |
| `groups/<slug>/events/<id>/` | GET/PATCH/DELETE | Yes | Admin for write |
| `groups/<slug>/events/<id>/members/` | GET/POST | Yes | Admin for POST |
| `groups/<slug>/events/<id>/members/<mid>/` | PATCH/DELETE | Yes | Admin only |
| `groups/<slug>/events/<id>/members/<mid>/participation/` | PATCH | Yes | Self-serve RSVP |
| `groups/<slug>/events/<id>/invites/` | POST | Yes | Admin only |
| `groups/<slug>/events/<id>/songs/` | GET/POST | Yes | Setlist |
| `groups/<slug>/events/<id>/songs/<esid>/` | PATCH/DELETE | Yes | Admin only |
| `invites/` | GET | Yes | Filter by ?status |
| `invites/pending-count/` | GET | Yes | Count badge |
| `invites/<id>/accept/` | POST | Yes | Creates Membership/EventMember |
| `invites/<id>/decline/` | POST | Yes | Marks declined |
| `song-suggestions/pending/` | GET | Yes | Admin: list pending |
| `song-suggestions/pending-count/` | GET | Yes | Admin: count badge |
| `song-suggestions/<id>/approve/` | POST | Yes | Admin: creates Song |
| `song-suggestions/<id>/reject/` | POST | Yes | Admin: marks rejected |

---

## Testing

Test suite must cover per feature:
- Happy path (correct role, valid data)
- Wrong role (403)
- Outsider/unauthorized (404 or 403)
- Unauthenticated (401)
- Invalid input (400 + error message)

Run tests locally before pushing:
```bash
cd backend && poetry run python manage.py test --verbosity=2
# or
cd backend && poetry run pytest
```

Test locations:
- `apps/accounts/tests.py` — full coverage (register, profile, password, search)
- `apps/groups/tests/test_permissions.py` — access control scenarios
- `apps/events/tests.py` — events, songs, suggestions
- `apps/invites/tests.py` — invite flow

---

## Environment Variables

Never commit `.env`. Use `.env.example` as template.

**Development** (SQLite):
```
SECRET_KEY=django-insecure-dev-key
DEBUG=True
ALLOWED_HOSTS=*
```

**Production** (PostgreSQL):
```
SECRET_KEY=<strong-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DB_NAME=escala_louvor
DB_USER=postgres
DB_PASSWORD=<secret>
DB_HOST=db.example.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Commits & Code Review

- One feature = one commit (or squashed)
- Commit message: imperative ("Add X", "Fix Y", not "Added", "Fixed")
- Reference issue if applicable (`Add event API (closes #123)`)
- Sign commits: `git config user.signingkey <GPG-key>`

---

## Dependency Management (Poetry)

All dependencies managed via Poetry. No `requirements.txt` — use `pyproject.toml` + `poetry.lock`.

**Backend dependencies** (`python ^3.10`):
- `django ^4.2`, `djangorestframework ^3.14`, `djangorestframework-simplejwt ^5.3`
- `django-cors-headers ^4.3`, `python-decouple ^3.8`
- `psycopg2-binary ^2.9` (PostgreSQL), `pillow ^12.2.0` (profile photos)
- Dev: `pytest ^7.4`, `pytest-django ^4.7`, `django-stubs ^4.2`

**Frontend dependencies** (`python ^3.11`):
- `flet` (cross-platform UI framework), `httpx` (async HTTP client)

**Backend setup:**
```bash
cd backend
poetry install                    # install from lock file
poetry add <package>              # add dependency
poetry remove <package>           # remove dependency
poetry update                     # update all (respects constraints)
poetry show                       # list all packages
poetry export -f requirements.txt # fallback if needed
```

**Frontend setup:**
```bash
cd frontend
poetry install
poetry add <package>
```

**Development env:** Poetry manages venv automatically. Activate:
```bash
poetry shell    # activate poetry venv
exit            # deactivate
```

Or run commands directly:
```bash
poetry run python manage.py runserver
poetry run pytest
```

---

## Tooling

- **Package Manager**: Poetry (deterministic, lock file, dev dependencies)
- **Tests**: Django unittest + DRF APITestCase (run via `poetry run pytest` or `python manage.py test`)
- **Linter**: (setup TBD — could use Flake8, Black)
- **Type hints**: (optional, not required yet)

---

## Resources

- Django Docs: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- SimpleJWT: https://django-rest-framework-simplejwt.readthedocs.io/
- Flet: https://flet.io/docs/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- SOLID: https://en.wikipedia.org/wiki/SOLID
