# Plan: Update CLAUDE.md to reflect actual project state

## Context

CLAUDE.md was written early and is now outdated. The project grew significantly: new apps, more frontend pages/modules, new config files. Docs and code diverged — misleads Claude and developers about what exists.

---

## Gaps Found (CLAUDE.md vs actual project)

### Backend — missing apps
- `invites/` app (models, views, serializers, urls, tests) — fully implemented
- `common/` app (instruments.py shared utility)

### Backend — missing dependency
- `pillow ^12.2.0` (image handling for profile photos)

### Frontend — outdated structure
CLAUDE.md shows skeleton. Actual frontend has:
- `authz.py` — authorization helpers
- `theme.py` — color/spacing tokens
- `instrument_icons.py` — icon mappings
- `components/styled.py` + `components/app_bar_user.py`
- `api/songs.py`, `api/song_suggestions.py`, `api/invites.py` (missing from docs)
- 15 pages (CLAUDE.md implied fewer)

### Frontend — Python version wrong
CLAUDE.md says nothing specific. Actual: `python = "^3.11"` (frontend `pyproject.toml`)

### Project root — missing files
- `PRD.md` — product requirements doc (exists)
- `.cursor/` — Cursor editor rules and skills (exists)
- `TEAM_AGENTS.md` in `.claude/` — multi-agent coordination doc (exists)
- `docker-compose.yml` referenced in CLAUDE.md but **does not exist**

### Settings
- `backend/escala/settings.py` exists alongside `settings/` directory — likely legacy; CLAUDE.md only documents the split settings (correct approach)

### Testing skill
- CLAUDE.md says `/create-tests apps/events/views.py` — skill `.claude/skills/create-tests/` does NOT exist in project
- Available skill is `frontend-refactor`
- Remove the `/create-tests` invocation examples; keep the test command + coverage requirements

### API table
- No API endpoint table in CLAUDE.md — adding one improves discoverability

---

## Changes to Make in CLAUDE.md

### 1. Project Structure section
- Add `invites/` app
- Add `common/` app
- Expand frontend tree with all actual files/dirs
- Add `PRD.md`, `.cursor/`, `TEAM_AGENTS.md`
- Remove `docker-compose.yml` (doesn't exist)

### 2. Dependencies section (new or inline)
- Backend: add `pillow`
- Frontend: Python 3.11+, `flet`, `httpx`

### 3. Testing section
- Remove `/create-tests` skill invocation (skill doesn't exist)
- Keep test run command and coverage requirements

### 4. API Endpoints section (new)
- Add complete endpoint reference table

### 5. Multi-Tenancy section
- Already accurate — keep as is

---

## Critical Files to Modify

- `CLAUDE.md` (root) — **only file to change**

---

## Verification

After update:
1. Read CLAUDE.md and confirm structure matches `ls` output of actual dirs
2. Confirm no references to non-existent files (docker-compose.yml, create-tests skill)
3. Confirm all apps listed match `backend/apps/` actual contents
