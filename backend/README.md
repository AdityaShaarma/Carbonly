# Carbonly Backend API

FastAPI backend for Carbonly - carbon accounting and emissions reporting platform.

## Quick Start (Local)

```bash
# 1. Create venv
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create PostgreSQL database (Mac Homebrew: uses current user by default)
createdb carbonly
# If you use a different user/password, set DATABASE_URL in .env

# 4. Copy env and configure
cp .env.example .env
# Edit .env: set DATABASE_URL if needed. For Mac local: postgresql+asyncpg://localhost:5432/carbonly
# (uses current OS user). For Docker postgres: postgresql+asyncpg://postgres:postgres@localhost:5432/carbonly

# 5. Run migrations
alembic upgrade head

# 6. Seed demo data (creates test user + emission factors)
python scripts/seed_dev.py

# 7. Start server
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000 | Docs: http://127.0.0.1:8000/docs

**Demo credentials:** test@carbonly.com / password123

## Docker

```bash
# Start Postgres + Backend
docker compose up -d

# Run migrations (from host, DB is on localhost:5432)
alembic upgrade head

# Seed
python scripts/seed_dev.py

# Backend runs at http://localhost:8000
```

Or run Postgres only and run backend locally:

```bash
docker compose up -d postgres
# Then: alembic upgrade head && python scripts/seed_dev.py && uvicorn app.main:app --reload
```

## Database

- **Alembic migrations:** `alembic upgrade head`
- **New migration:** `alembic revision --autogenerate -m "description"`
- **Local Mac:** Default `postgresql+asyncpg://localhost:5432/carbonly` uses current OS user (no password). Create DB with `createdb carbonly`.
- **Docker Postgres:** `postgresql+asyncpg://postgres:postgres@localhost:5432/carbonly`

## Dev-Only Endpoints

When `DEBUG=true` or `ENV=local`:

- `POST /api/auth/dev-seed` - Seed demo company + user + emission factors
- `GET /api/auth/dev-db-check` - DB connectivity and user count

## Tests

```bash
# Ensure DEBUG=true or ENV=local, DB is set up, and dev-seed has been run
pytest tests/ -v
```

## Linting & Formatting

```bash
ruff check app tests
black app tests
```

## API Endpoints

### Auth

- `POST /api/auth/login` - Login, returns JWT
- `GET /api/auth/me` - Current user + company

### Dashboard

- `GET /api/dashboard?year=2025` - Full dashboard payload
- `POST /api/dashboard/recompute?year=2025` - Recompute emissions

### Integrations

- `GET /api/integrations` - List connections (creates aws/gcp/azure defaults)
- `POST /api/integrations/{provider}/sync` - Sync (mock data)
- `POST /api/integrations/{provider}/estimate` - AI estimated
- `POST /api/integrations/manual/activity` - Single manual record
- `POST /api/integrations/manual/upload` - CSV upload (multipart file)

### Reports

- `GET /api/reports?year=2025` - List reports
- `POST /api/reports` - Create draft
- `GET /api/reports/{id}` - Detail
- `POST /api/reports/{id}/publish` - Publish + share token
- `GET /api/reports/{id}/pdf` - PDF download
- `GET /api/reports/r/{share_token}` - Public share (no auth)

### Company

- `GET /api/company` - Profile
- `PUT /api/company` - Update profile
- `PUT /api/company/preferences` - Preferences
- `DELETE /api/company/data` - Delete all data (confirm required)

### Insights

- `GET /api/insights?year=2025` - Reduction recommendations (mocked)

## Health

- `GET /` - Basic health
- `GET /health` - Health + DB connectivity check
