# Carbonly Frontend

React + TypeScript frontend for Carbonly (carbon accounting and emissions reporting). Connects to the FastAPI backend.

## Setup

1. **Environment**

   ```bash
   cp .env.example .env
   ```

   Set `VITE_API_BASE_URL=http://127.0.0.1:8000` (or your backend URL).

2. **Install and run**

   ```bash
   npm install
   npm run dev
   ```

   App runs at **http://localhost:5173**.

## Backend and seed

1. Start the backend (see `backend/README.md`): run Postgres, `alembic upgrade head`, then `python scripts/seed_dev.py` or call `POST /api/auth/dev-seed` with `DEBUG=true` or `ENV=local`.
2. Log in with **test@carbonly.com** / **password123**.

## Flow

- **Connect integrations:** Go to Integrations → choose a provider (e.g. AWS) → click **Sync** or **Use AI estimate**. Backend creates mock activities and recomputes emissions.
- **Dashboard:** After sync or manual data, open Dashboard and use **Recompute** if needed. You’ll see company stats, total footprint, data quality, and monthly trend chart.
- **Reports:** Reports → **Create report** (title + year) → open the report → **Publish** → **Download PDF**. Use **Copy** on the share link to open the public read-only page (e.g. `/r/{token}`).
- **Onboarding:** After first login, you’ll see the onboarding checklist if there are no integrations/manual data/reports yet.
- **Methodology:** Settings → Methodology page explains measured vs estimated, scopes, and factor sources.

## CORS

Backend must allow the frontend origin (e.g. `http://localhost:5173`) and credentials. If you see CORS errors, set `CORS_ORIGINS` in the backend `.env` to include that URL.

## Scripts

- `npm run dev` – start dev server
- `npm run build` – production build
- `npm run lint` – ESLint
- `npm run preview` – preview production build
