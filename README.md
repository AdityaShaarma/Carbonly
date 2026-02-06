# Carbonly

Carbonly is a carbon accounting and emissions reporting platform for B2B SaaS SMBs.

## Local Development

Backend (FastAPI + Postgres + Alembic):

1. `cd backend`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `cp .env.example .env` and update values as needed
5. `alembic upgrade head`
6. `python scripts/seed_dev.py`
7. `uvicorn app.main:app --reload`

Frontend (Vite + React + Tailwind):

1. `cd frontend`
2. `npm install`
3. `cp .env.example .env` and set `VITE_API_BASE_URL=http://127.0.0.1:8000`
4. `npm run dev`

## Environment Variables

Backend (`backend/.env`):

- `ENV` = `local|development|staging|production`
- `DEBUG` = `true|false`
- `DATABASE_URL` = Postgres URL (Render may provide `postgres://` which is normalized)
- `SECRET_KEY` = long random string (min 32 chars in prod)
- `CORS_ORIGINS` = comma-separated list, e.g. `https://your-vercel.app`
- `ENABLE_DOCS` = `true|false` (docs disabled in prod by default)
- `TRUST_PROXY_HEADERS` = `true|false`
- `RATE_LIMIT_ENABLED` = `true|false` (MVP in-memory limiter)

Frontend (`frontend/.env`):

- `VITE_API_BASE_URL` = Render backend URL (empty string uses same-origin)
- `VITE_DEMO_MODE` = `true|false`

## Deploy: Render (Backend + Postgres)

Use `render.yaml` at repo root.

Render Web Service:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `bash render_start.sh`
- Instance: single instance (rate limiting is in-memory)

Required Render env vars:

- `DATABASE_URL` (from Render Postgres)
- `SECRET_KEY` (secure random)
- `ENV=production`
- `DEBUG=false`
- `ENABLE_DOCS=false` (set `true` temporarily if needed)
- `TRUST_PROXY_HEADERS=true`
- `RATE_LIMIT_ENABLED=true`
- `CORS_ORIGINS=https://your-vercel-domain.vercel.app`

Migrations are executed on startup by `backend/render_start.sh`.

## Deploy: Vercel (Frontend)

Project settings:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

Env vars:

- `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com`
- `VITE_DEMO_MODE=false` (optional)

`frontend/vercel.json` enables SPA routing.

## Security Notes (MVP)

- Auth uses Argon2 for password hashing.
- JWT is stored in `localStorage` for the prototype (documented risk; acceptable for MVP).
- Security headers are set at the backend:
  - `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, basic CSP.
- OpenAPI docs are disabled in production unless `ENABLE_DOCS=true`.
- In-memory rate limiting is enabled by default and should be replaced by Redis for multi-instance.

## Migrations

Local:

- `cd backend`
- `alembic upgrade head`

Render:

- Migrations run automatically on startup via `render_start.sh`.

## Smoke Test Checklist

1. Seed demo data (local only): `python backend/scripts/seed_dev.py`
2. Login → Dashboard loads
3. Integrations sync → Dashboard totals update
4. Create report → Publish → Public link works
5. Download PDF works
6. `/health` and `/health/details` return healthy

## Production Checklist

- `ENV=production`
- `SECRET_KEY` is strong and unique
- `DATABASE_URL` set from Render
- `CORS_ORIGINS` set to Vercel URL
- `ENABLE_DOCS=false` unless explicitly needed
- `VITE_API_BASE_URL` points to Render backend
- CI green (backend compile + tests, frontend build)

## Deploy Commands (Quick Reference)

Render:

1. Create Render Postgres instance
2. Create Render web service using `render.yaml`
3. Set env vars (see above)

Vercel:

1. Import repo
2. Set root dir to `frontend`
3. Set `VITE_API_BASE_URL`
4. Deploy
