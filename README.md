# Chess Web App

Starter boilerplate with a React + TypeScript frontend and a Python FastAPI backend.

## Prerequisites

- Node.js 20.19+ or 22.12+
- Python 3.11+

## Run the backend

Start PostgreSQL from the repository root (Docker Compose is used for the database only):

```powershell
docker compose up -d db
```

In another terminal from the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000. Interactive API docs are at http://127.0.0.1:8000/docs.

Tables are created automatically for this starter. Before production, replace this with Alembic migrations, set `SESSION_COOKIE_SECURE=true`, and configure SMTP in `backend/.env`. In development without SMTP, verification and reset links are printed in the backend log.

### Authentication API

- `POST /api/auth/register` — create an unverified account and send a verification link.
- `POST /api/auth/verify-email` — verify with `{ "token": "..." }`.
- `POST /api/auth/verify-email/resend` — request another verification email.
- `POST /api/auth/login` — sign in with `{ "email": "...", "password": "..." }`; sets an HttpOnly session cookie.
- `POST /api/auth/logout` — revoke the current session and clear its cookie.
- `GET /api/auth/me` — return the signed-in user.
- `POST /api/auth/password-reset/request` — request a reset email; response does not reveal whether the address exists.
- `POST /api/auth/password-reset/confirm` — reset with `{ "token": "...", "new_password": "..." }`; revokes all active sessions.

Verification and reset links currently lead to frontend routes that still need pages wired up. The API endpoints can be exercised from the docs, and development links appear in the backend log.

## Run the frontend

In another terminal from the repository root:

```powershell
npm install
npm run dev
```

Open the URL printed by Vite (usually http://localhost:5173). Vite proxies `/api` requests to the backend.

## Current starter endpoint

- `GET /api/health` — confirms the API is running; the frontend displays its connection status.
