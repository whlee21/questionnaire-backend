# AGENTS.md — PushNotify Firebase Push Notification Sender Console

## Project Layout

```
backend/     FastAPI + Python 3.12 (async SQLAlchemy, Alembic, firebase-admin)
frontend/    React 19 + Vite 8 + TypeScript (vitest, Playwright)
docs/        API contract, client integration guide, Firebase setup guide
scripts/     seed_admin.py, smoke.sh
```

## Quick Start

```bash
cp backend/.env.example backend/.env   # edit ADMIN_EMAIL, ADMIN_PASSWORD
docker compose up -d                   # starts db + backend + frontend
curl http://localhost:8000/health      # → {"status":"ok"}
# Frontend: http://localhost:5173
```

## Developer Commands

### Backend
```bash
cd backend

# Run all tests (no DB needed — DB test skips gracefully)
PYENV_VERSION=3.12.3 pyenv exec python -m pytest -q

# Lint
PYENV_VERSION=3.12.3 pyenv exec ruff check .

# Apply DB migrations (requires running postgres)
PYENV_VERSION=3.12.3 pyenv exec alembic upgrade head

# Generate a new migration after model changes
PYENV_VERSION=3.12.3 pyenv exec alembic revision --autogenerate -m "description"

# Seed admin user (idempotent)
PYENV_VERSION=3.12.3 pyenv exec python scripts/seed_admin.py

# Start dev server
PYENV_VERSION=3.12.3 pyenv exec uvicorn app.main:create_app --factory --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run test -- --run    # run all tests
npx tsc --noEmit         # type check
npm run dev              # dev server
```

### Full Stack
```bash
make up           # docker compose up -d
./scripts/smoke.sh  # end-to-end smoke test (requires stack running)
make down
```

## CRITICAL: FCM_FAKE Mode (Zero-Device Testing)

**`FCM_FAKE=1` is the default in `docker-compose.yml` and for all CI/QA.**

- With `FCM_FAKE=1`: entire stack runs without Firebase credentials or real devices.
- All automated QA (pytest, vitest, smoke.sh) uses this mode.
- Real Firebase credentials only needed for live production sends.
- To use real Firebase: set `FCM_FAKE=0` and `GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccount.json` in `backend/.env`.

## CRITICAL: Secrets — Never Commit

The `.gitignore` blocks all Firebase secret patterns:
```
**/serviceAccount*.json   **/firebase-*.json
**/*-adminsdk-*.json      **/*.pem
```

**Never log raw FCM tokens.** The backend `_FcmTokenScrubFilter` redacts tokens (100+ char strings) from all log output.

## FCM Constraints (Devs Trip On These)

| Constraint | Value |
|---|---|
| Multicast batch limit | ≤ 500 tokens per `send_many()` call |
| Topic subscribe/unsubscribe batch | ≤ 1000 tokens per call |
| `data` field values | MUST be strings — FCM rejects non-string values |
| Legacy server-key API | DEPRECATED (June 2024) — do NOT use |
| `firebase-admin` SDK | Synchronous — MUST wrap in `run_in_threadpool` in async FastAPI routes |
| Broadcast | Sends to reserved `all` topic; devices auto-subscribed on registration |
| Token cleanup | Invalidate on `UNREGISTERED` or `INVALID_ARGUMENT` only; `OTHER` errors are transient |

## Python Environment

This project uses **pyenv 3.12.3**. The system Python may be 3.11.x.

Always prefix Python/pytest/alembic commands with:
```bash
PYENV_VERSION=3.12.3 pyenv exec <command>
```

## Known Gotchas

- **passlib + bcrypt>=4.0**: `passlib` raises `ValueError: password cannot be longer than 72 bytes`. Project uses `bcrypt` directly. Do NOT add passlib back.
- **slowapi rate limits in tests**: `test_auth.py` fires 3 login calls (under 5/min limit). `test_security.py` fires 7 to trigger 429. Run full suite, not individual files.
- **`AdminUser.__new__(AdminUser)`**: Raises `AttributeError` when setting mapped attrs. Use `MagicMock(spec=AdminUser)` for test fixtures.
- **`HTTPBearer` returns 401** (not 403) when `Authorization` header is absent.
- **Node.js v26 `localStorage`**: `setupTests.ts` already mocks it. Do NOT remove this mock.
- **Login page heading**: Use `getByRole('heading', { name: /pushnotify/i })` — the h1 says "PushNotify", not "Login".
- **`Table<T>` generic**: Cast page data via `items as unknown as Record<string, unknown>[]`.

## Reference Docs

- `docs/api-contract.md` — all 12 endpoints with request/response schemas
- `docs/client-integration.md` — iOS/Android/Web FCM token registration guide
- `docs/firebase-setup.md` — Firebase project setup, VAPID, APNs, google-services.json
