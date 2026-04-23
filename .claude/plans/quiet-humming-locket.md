# Simplify: Code Review Plan

## Context

Full codebase review (v1, single commit). No uncommitted changes. Three agents reviewed for reuse, quality, and efficiency. Findings below ordered by impact.

---

## Findings & Fixes

### 1. N+1 Queries — Event list counts (CRITICAL)

**File:** `backend/apps/events/serializers.py:206-207`

`EventListSerializer` calls `.count` via `source=` for every event in the list — 2 extra queries per event.

**Fix:** Annotate in the view queryset instead:
```python
# events/views.py — EventListView.get()
queryset = Event.objects.filter(group=group).annotate(
    member_count=Count('event_members', distinct=True),
    song_count=Count('event_songs', distinct=True),
)
```
Remove `source='event_members.count'` from serializer, use `read_only=True` IntegerField directly.

---

### 2. Sequential frontend loads (CRITICAL)

**File:** `frontend/pages/group_page.py:277-280`

Four independent loads run sequentially via `page.run_task()`. No dependency between them.

**Fix:** Parallelize with `asyncio.gather`:
```python
await asyncio.gather(load_group(), load_events(), load_members(), load_songs())
```

**File:** `frontend/pages/config_event_members_page.py:434-447`

`get_members` and `list_event_members` are independent — can run together after `get_event`.

**Fix:**
```python
event = await get_event(client, slug, event_id)
group_members, event_members = await asyncio.gather(
    get_members(client, slug),
    list_event_members(client, slug, event_id),
)
```

---

### 3. GroupScopedMixin not reused (HIGH)

**Files:** `backend/apps/events/views.py:21-31` defines `GroupScopedMixin`.
`backend/apps/groups/views.py` and `backend/apps/invites/views.py` reimplement the same `get_group()` / permission logic inline.

**Fix:** Move `GroupScopedMixin` to `backend/apps/common/mixins.py`. Import and use in all three view files.

---

### 4. `_user_instruments_list()` duplicated (HIGH)

**Files:**
- `backend/apps/events/serializers.py:11-15`
- `backend/apps/invites/views.py:21-25`

Identical function defined twice.

**Fix:** Move to `backend/apps/accounts/utils.py`. Import from both files.

---

### 5. Date formatting duplicated across 3 pages (HIGH)

**Files:**
- `frontend/pages/event_detail_page.py:31-39`
- `frontend/pages/group_page.py:52-60`
- `frontend/pages/config_events_page.py:12-24`

Each defines `_format_event_date()` / `_parse_api_datetime()` independently.

**Fix:** Create `frontend/utils/date_utils.py` with one `format_event_date(value: str) -> str`. Import in all three.

---

### 6. `APIError.detail` extraction duplicated (HIGH)

**Pattern:** `d = ex.detail; msg = d if isinstance(d, str) else str(d)` appears 6+ times across pages and invites_page.py.

**Fix:** Add `@property` to `APIError` in `frontend/api/client.py`:
```python
@property
def message(self) -> str:
    return self.detail if isinstance(self.detail, str) else str(self.detail)
```
Replace all instances with `ex.message`.

---

### 7. Redundant `load_context()` after mutations (HIGH)

**File:** `frontend/pages/config_event_members_page.py:103, 306, 320`

After sending invite or modifying a member, `load_context()` re-fetches all 3 endpoints. Only event_members changed.

**Fix:** After mutations, only refresh event_members:
```python
nonlocal event_members
event_members = await list_event_members(client, slug, event_id)
rebuild_list()
```

---

### 8. Missing DB indexes on Invite (MEDIUM)

**File:** `backend/apps/invites/models.py` — `Invite.Meta`

Frequent queries filter on `(invitee, status)` and `(invitee, kind, status)`.

**Fix:** Add to `Invite.Meta`:
```python
indexes = [
    models.Index(fields=['invitee', 'status']),
    models.Index(fields=['invitee', 'kind', 'status']),
]
```

---

### 9. Duplicate admin_group_ids query (MEDIUM)

**File:** `backend/apps/events/views.py:385-406`

`SongSuggestionPendingListView` and `SongSuggestionPendingCountView` both run the same `Membership.objects.filter(user=..., role='admin')` query.

**Fix:** Extract to a mixin method `get_admin_group_ids(user)` shared by both views.

---

### 10. Nested conditionals in ParticipationView (MEDIUM)

**File:** `backend/apps/events/views.py:220-228`

3-level nested if/elif/else for ownership check, all branches raise same error.

**Fix:** Flatten to single expression:
```python
is_owner = (
    (event_member.membership_id and event_member.membership.user_id == user.id)
    or (event_member.guest_user_id and event_member.guest_user_id == user.id)
)
if not is_owner:
    raise Http404('Participação não encontrada.')
```

---

### 11. SongSuggestion approve/reject duplicated transaction block (MEDIUM)

**File:** `backend/apps/events/views.py:412-461`

Both views duplicate: lock suggestion, check admin, check pending status, then diverge.

**Fix:** Extract to `_get_pending_suggestion(pk, user)` helper that returns the locked suggestion or raises. Both views call it then apply their specific action.

---

### 12. `client.py` retry logic duplicated (MEDIUM)

**File:** `frontend/api/client.py:45-126`

401 refresh-and-retry logic implemented twice — once in `_request()`, once in `post_multipart()`.

**Fix:** Extract `_execute_with_retry(build_request_fn)` coroutine. Both methods call it.

---

### 13. Hardcoded BASE_URL (MEDIUM)

**File:** `frontend/api/client.py:14`

```python
BASE_URL = 'http://localhost:8000/api/v1'
```

**Fix:** Read from env or `frontend/constants.py`:
```python
import os
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api/v1')
```

---

### 14. Unnecessary comments explaining WHAT (LOW)

Remove docstrings/inline comments that restate what the code already says clearly. Key examples:
- `event_detail_page.py` — `"""Retorna (nome_do_icone, cor)..."`
- `config_events_page.py` — `# --- Form state ---` blocks

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/apps/common/mixins.py` | NEW — GroupScopedMixin |
| `backend/apps/accounts/utils.py` | NEW — `_user_instruments_list` |
| `backend/apps/events/views.py` | Use mixin; annotate queryset; fix ParticipationView; extract helpers |
| `backend/apps/events/serializers.py` | Remove `.count` source fields |
| `backend/apps/groups/views.py` | Use GroupScopedMixin |
| `backend/apps/invites/views.py` | Use GroupScopedMixin; import utils |
| `backend/apps/invites/models.py` | Add indexes |
| `frontend/utils/date_utils.py` | NEW — `format_event_date` |
| `frontend/api/client.py` | Add `APIError.message`; extract retry; env BASE_URL |
| `frontend/pages/group_page.py` | asyncio.gather for loads; use date_utils |
| `frontend/pages/config_event_members_page.py` | gather loads; targeted refresh after mutation |
| `frontend/pages/event_detail_page.py` | use date_utils; remove unnecessary comment |
| `frontend/pages/config_events_page.py` | use date_utils |
| `frontend/pages/invites_page.py` | use `ex.message` |

---

## Verification

```bash
# Backend tests
cd backend && poetry run python manage.py test --verbosity=2

# Check migrations apply cleanly
cd backend && poetry run python manage.py makemigrations --check
cd backend && poetry run python manage.py migrate

# Frontend: run app and manually test
# - Group page loads (all 4 sections appear)
# - Event members page (invite + member list refresh correctly)
# - Invite accept/decline flow
```
