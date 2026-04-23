# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Backend

```bash
cd backend
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver          # http://localhost:8000
```

**Tests** — run per app (global discovery breaks on `groups/tests/` directory structure):
```bash
cd backend
poetry run python manage.py test apps.accounts apps.events apps.invites --verbosity=2
# single test class:
poetry run python manage.py test apps.events.tests.EventListTests --verbosity=2
```

**Migrations:**
```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
poetry run python manage.py makemigrations --check   # CI: verify no pending migrations
```

### Frontend

```bash
cd frontend
poetry install
poetry run flet run main.py    # http://localhost:8550
```

---

## Architecture

### Backend layers

```
Models      → schema, domain validation, Meta, relations — no HTTP imports
Serializers → validate/transform payload — no heavy queries
Views       → HTTP, queryset filters, permission checks, orchestration
Permissions → authorization only (IsGroupMember, IsGroupAdmin)
```

All views inherit `GroupScopedMixin` (`backend/apps/common/mixins.py`) which provides:
- `get_group()` — resolves group by `slug` from URL kwargs
- `check_group_permission(permission_class)` — raises PermissionDenied on failure

### Multi-tenancy (critical)

Every resource belongs to a `Group`. **Always** filter by group derived from the URL slug — never trust client-supplied `group_id`:

```python
# every queryset:
Event.objects.filter(group=self.get_group())

# never:
Event.objects.all()
Event.objects.get(pk=pk)                         # leaks across groups
Group.objects.get(pk=request.data['group_id'])   # attacker-controlled
```

### Shared utilities

| File | Purpose |
|------|---------|
| `backend/apps/common/mixins.py` | `GroupScopedMixin` — used by all group-scoped views |
| `backend/apps/common/instruments.py` | `INSTRUMENT_CHOICES`, `validate_instruments_list()` |
| `backend/apps/accounts/utils.py` | `get_user_instruments(user)` — safe profile.instruments access |
| `frontend/utils/date_utils.py` | `format_event_date(value)` — ISO → `dd/mm/yyyy HH:MM` |

### Frontend page contract

Every page is a function `build_<name>_page(page: ft.Page, state: AppState, ...) -> ft.View` in `frontend/pages/`.

- **State**: `AppState` + `page.session`; single source of truth
- **API calls**: `APIClient(state, page)` + functions from `frontend/api/*`; handle `APIError` with `ex.message` (property on `APIError`)
- **Visuals**: tokens from `theme.py` (`COLORS`, `SPACING`, `FONT_SIZES`); components from `components/styled.py` (`FormField`, `PrimaryButton`, `ErrorText`, `SurfaceCard`, `EmptyState`, etc.) — never inline literals
- **Routing**: register in `frontend/main.py` — more specific routes before generic ones
- **Async**: all API handlers `async def` with `await`; `page.run_task()` for initial loads; `asyncio.gather()` for independent parallel loads
- **Updates**: mutate controls, then one `page.update()` at the end of handler — never inside a tight loop

### EventMember XOR constraint

`EventMember` always has exactly one of: `membership` (group member) or `guest_user` (invited external). Never both, never neither.

### Invite flow

Accepting an invite runs in `transaction.atomic` and creates either `Membership` (group invite) or `EventMember` (event invite). Invites have DB-level unique constraints for pending status.

---

## Code rules

### Access control (every endpoint)

- Permission class required: `IsGroupMember` (read) or `IsGroupAdmin` (write)
- Unauthorized → 403 or 404, never 200
- Group context always from URL slug, never from request body

### QuerySet performance

- Event list queries use `.annotate(member_count=Count(...), song_count=Count(...))` — do not use `source='relation.count'` in serializers (N+1)
- Use `select_related` / `prefetch_related` on nested serializers
- `Invite` has indexes on `(invitee, status)` and `(invitee, kind, status)`

### Frontend error handling

```python
except APIError as ex:
    error_msg.value = ex.message   # use .message property, not raw .detail
    error_msg.visible = True
    page.update()
```

---

## Testing checklist (per feature)

- Happy path (correct role, valid data) → 200/201
- Wrong role → 403
- Outsider (not in group) → 404 or 403
- Unauthenticated → 401
- Invalid input → 400 with field errors

---

## Environment variables

Dev (SQLite, auto-created):
```
SECRET_KEY=django-insecure-dev-key
DEBUG=True
ALLOWED_HOSTS=*
```

Production (PostgreSQL):
```
SECRET_KEY=<strong-random>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DB_NAME=escala_louvor
DB_USER=postgres
DB_PASSWORD=<secret>
DB_HOST=db.example.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

Frontend API URL:
```
API_BASE_URL=http://localhost:8000/api/v1   # default if unset
```
