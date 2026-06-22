# ELD Trip Planner & Daily Log Generator

Full-stack FMCSA Hours-of-Service trip planning tool. Given a current location, pickup, dropoff, and rolling 70-hour cycle usage, the app computes a compliant multi-day driving schedule and renders route maps plus FMCSA-style daily log sheets.

## Stack

| Layer | Tech | Deployment |
|---|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS 4, Leaflet | **Vercel** |
| Backend | Django 5, DRF, Gunicorn, WhiteNoise | **Railway** (or Render) |
| Routing | OpenRouteService (optional) or OSRM + Nominatim | — |

## Architecture

```
┌─────────────────────┐         REST/JSON          ┌──────────────────────────┐
│   Next.js Frontend   │ ─────────────────────────► │   Django + DRF Backend    │
│   (Vercel)           │ ◄───────────────────────── │   (Railway / Render)      │
└──────────┬──────────┘                              └────────────┬─────────────┘
           │ Leaflet / OSM tiles                                  │ geocode + route
           ▼                                                      ▼
   NEXT_PUBLIC_API_URL                              POST /api/plan-trip/
```

**Repository layout** — deploy independently:

```
ELD/
├── backend/          ← Railway / Render (root directory = backend)
├── frontend/         ← Vercel (root directory = frontend)
└── README.md
```

---

## Local development

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

API: `http://localhost:8000`  
Health check: `GET http://localhost:8000/api/health/`

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

App: `http://localhost:3000`

### Run tests

```bash
cd backend
python manage.py test tripplanner.tests
```

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Production | Random secret. Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | Yes | `True` locally, **`False` in production** |
| `ALLOWED_HOSTS` | Production | Comma-separated hostnames, e.g. `your-app.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | Production | Comma-separated frontend URLs, e.g. `https://your-app.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | Optional | HTTPS origins for CSRF; defaults to https entries from CORS |
| `ORS_API_KEY` | Optional | OpenRouteService key; falls back to OSRM/Nominatim |
| `DATABASE_URL` | Optional | PostgreSQL URL; **not required** (see Database section) |
| `CORS_ALLOW_VERCEL_PREVIEWS` | Optional | `true` to allow all `*.vercel.app` preview URLs |
| `WEB_CONCURRENCY` | Optional | Gunicorn workers (default `2`) |
| `GUNICORN_TIMEOUT` | Optional | Request timeout seconds (default `120`) |

Railway and Render automatically set `RAILWAY_PUBLIC_DOMAIN` / `RENDER_EXTERNAL_HOSTNAME` — these are appended to `ALLOWED_HOSTS`.

### Frontend (`frontend/.env.local` / Vercel)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Production | Backend URL **without trailing slash**, e.g. `https://your-api.up.railway.app` |

---

## Database

**No application database is required.** The trip planner is stateless — one request in, one computed plan out. There are no Django models in `tripplanner`.

Django still needs a database for its internal tables (migrations, sessions framework). **SQLite is sufficient** and is the default. `start.sh` runs `migrate` on each deploy.

Optional: set `DATABASE_URL` to a Railway/Render PostgreSQL instance if you prefer Postgres for Django internals. This does not change application behavior.

---

## Deploy backend — Railway (recommended)

### 1. Create project

1. Push this repo to GitHub.
2. [Railway](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Set **Root Directory** to `backend`.

### 2. Environment variables

In Railway → **Variables**:

| Variable | Value |
|---|---|
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | *(generate a random key)* |
| `ALLOWED_HOSTS` | `your-service.up.railway.app` *(your Railway domain)* |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.vercel.app` *(set after Vercel deploy)* |
| `ORS_API_KEY` | *(optional)* |

### 3. Build & start (auto-detected)

Railway uses `railway.toml` and `start.sh`:

- **Build:** `pip install -r requirements.txt` (Nixpacks)
- **Start:** `bash start.sh` → migrate → collectstatic → Gunicorn
- **Health check:** `GET /api/health/`

### 4. Generate domain

Railway → **Settings** → **Networking** → **Generate Domain**.

Copy the public URL (e.g. `https://eld-api-production.up.railway.app`).

### 5. Verify

```bash
curl https://your-api.up.railway.app/api/health/
# {"status":"ok"}
```

---

## Deploy backend — Render (alternative)

### Option A: Blueprint

1. Render Dashboard → **New** → **Blueprint**.
2. Connect repo — Render reads `render.yaml` at repo root.
3. Set `CORS_ALLOWED_ORIGINS` and `ALLOWED_HOSTS` in the service environment.

### Option B: Manual web service

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| Start Command | `bash start.sh` |
| Health Check Path | `/api/health/` |

Environment variables: same as Railway table above. Render sets `RENDER_EXTERNAL_HOSTNAME` automatically.

---

## Deploy frontend — Vercel

### 1. Import project

1. [Vercel](https://vercel.com) → **Add New** → **Project** → import GitHub repo.
2. Set **Root Directory** to `frontend`.
3. Framework Preset: **Next.js** (auto-detected).

### 2. Environment variables

| Variable | Value | Environments |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://your-api.up.railway.app` | Production, Preview, Development |

**No trailing slash.**

### 3. Build settings

| Setting | Value |
|---|---|
| Build Command | `npm run build` |
| Output Directory | `.next` (default) |
| Install Command | `npm install` |

`frontend/vercel.json` documents these defaults.

### 4. Deploy & connect CORS

After Vercel deploys, copy your production URL (e.g. `https://eld-trip-planner.vercel.app`).

Update Railway/Render backend:

```
CORS_ALLOWED_ORIGINS=https://eld-trip-planner.vercel.app
CSRF_TRUSTED_ORIGINS=https://eld-trip-planner.vercel.app
```

Redeploy backend if needed.

### 5. Verify end-to-end

1. Open Vercel URL.
2. Submit Dallas, TX → Denver, CO.
3. Confirm map, compliance panel, and log sheets load.

---

## Deployment checklist

Use this after deploying both services:

- [ ] `GET https://<backend>/api/health/` returns `{"status":"ok"}`
- [ ] Backend `DJANGO_DEBUG=False` and `DJANGO_SECRET_KEY` is set
- [ ] `ALLOWED_HOSTS` includes backend domain
- [ ] `CORS_ALLOWED_ORIGINS` includes exact Vercel URL (with `https://`)
- [ ] Vercel `NEXT_PUBLIC_API_URL` points to backend (no trailing slash)
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Backend tests pass: `cd backend && python manage.py test`
- [ ] Trip form submits without CORS errors (browser DevTools → Network)
- [ ] Map renders (Leaflet loads client-side only)
- [ ] Log sheets and compliance panel appear on results page
- [ ] Long trip (e.g. Dallas → Seattle) returns multi-day logs

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| CORS error in browser | Frontend origin not in `CORS_ALLOWED_ORIGINS` | Add exact Vercel URL with `https://`; redeploy backend |
| `502` / timeout on plan-trip | Geocoding/routing slow | Increase `GUNICORN_TIMEOUT`; add `ORS_API_KEY` |
| `DisallowedHost` | Missing `ALLOWED_HOSTS` | Add Railway/Render domain; platform env vars auto-append |
| `NEXT_PUBLIC_API_URL is not configured` | Missing Vercel env var | Set in Vercel → Settings → Environment Variables; redeploy |
| `DJANGO_SECRET_KEY must be set` | Production without secret | Set `DJANGO_SECRET_KEY` on Railway/Render |
| Map works locally, not prod | API unreachable | Verify `NEXT_PUBLIC_API_URL` and CORS |
| Admin static files broken | Expected — API-only app | `/admin/` not required for assessment |

### Test CORS locally with production settings

```bash
# backend/.env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-local-test-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## API

**`POST /api/plan-trip/`**

```json
{
  "current_location": "Dallas, TX",
  "pickup_location": "Dallas, TX",
  "dropoff_location": "Denver, CO",
  "current_cycle_used_hours": 10
}
```

**`GET /api/health/`** — deployment health check.

---

## FMCSA rules (summary)

11-hour driving · 14-hour duty window · 30-minute break after 8h driving · 70-hour/8-day cycle · 10-hour reset · 34-hour restart. Calendar-day log totals may exceed 11h when a duty period crosses midnight — see Duty Period Analysis on the results page.

## Tests

```bash
cd backend && python manage.py test tripplanner.tests
```

13 tests: HOS engine, log builder, enrichment, health endpoint, API contract.
