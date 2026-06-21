# ELD Trip Planner & Daily Log Generator

Full-stack FMCSA Hours-of-Service trip planning tool. Given a current location, pickup, dropoff, and rolling 70-hour cycle usage, the app computes a compliant multi-day driving schedule and renders route maps plus FMCSA-style daily log sheets.

**Designed for assessment reviewers:** the results page includes a compliance audit, duty-period breakdown, event timeline, stop explanations, and an optional Assessment Review panel.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS 4, Leaflet |
| Backend | Django 5, Django REST Framework |
| Routing / geocoding | OpenRouteService (optional API key) or OSRM + Nominatim fallback |

## Architecture

```
┌─────────────────────┐         REST/JSON          ┌──────────────────────────┐
│   Next.js Frontend   │ ─────────────────────────► │   Django + DRF Backend    │
│   (Vercel)           │ ◄───────────────────────── │   (Render / Railway)      │
└──────────┬──────────┘                              └────────────┬─────────────┘
           │ map tiles (Leaflet/OSM)                              │
           │                                                      │ geocode + route
           ▼                                                      ▼
┌─────────────────────┐                              ┌──────────────────────────┐
│  OpenStreetMap       │                              │  ORS / OSRM + Nominatim   │
└─────────────────────┘                              └──────────────────────────┘

Backend service pipeline (single POST /api/plan-trip/):

  route_engine  →  hos_engine  →  log_builder  →  plan_enrichment
  (geocode/route)  (FMCSA sim)    (daily logs)     (compliance, duty periods,
                                                     timeline, explanations)
```

## Project structure

```
ELD/
├── backend/
│   └── tripplanner/services/
│       ├── route_engine.py      # Geocoding + routing
│       ├── hos_engine.py          # FMCSA simulation (core logic)
│       ├── fuel_engine.py         # Fuel interval helpers
│       ├── log_builder.py         # Daily log sheets + timestamps
│       └── plan_enrichment.py     # Compliance audit, duty periods, reviewer stats
├── frontend/
│   └── components/
│       ├── compliance/            # ComplianceSummary, DutyPeriodAnalysis, HOSExplanation
│       ├── trip/                  # TripTimeline, StopDetailsPanel
│       └── reviewer/              # Assessment Review panel
└── blank-paper-log.png
```

## Quick start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000** → submit a trip → review results at `/results`.

## HOS engine (how it works)

The HOS engine (`hos_engine.py`) simulates a trip as a sequence of duty-status events:

1. Optional deadhead drive (current → pickup)
2. **1-hour on-duty pickup** (assessment assumption)
3. Driving loop with FMCSA rules applied each step:
   - Max **11 hours driving** per duty period
   - Max **14-hour duty window** (non-pausing; includes breaks)
   - **30-minute break** after 8 cumulative hours of driving
   - **10-hour off-duty reset** when daily limits are reached
   - **34-hour restart** when the 70-hour cycle is exhausted
   - **Fuel stop** every 1,000 miles (30-min on-duty)
4. **1-hour on-duty dropoff**

The 11-hour and 14-hour clocks run **simultaneously** — whichever limit is hit first forces a stop.

## Duty period vs. calendar day (critical)

| Concept | Definition |
|---|---|
| **Duty period** | Starts at first on-duty/driving after a 10+ hour off-duty reset; ends at next 10+ hour reset |
| **Calendar day (log sheet)** | Midnight-to-midnight bucket for FMCSA daily log display |

**A single duty period can span two calendar days.** When it crosses midnight, the log sheet splits the driving block — so Day 2 might show 13.5h driving and Day 3 might show 13.0h driving, while each **duty period** still respects the 11-hour limit.

The **Duty Period Analysis** panel on the results page shows per-period totals so reviewers can verify compliance without misreading calendar-day totals.

## Compliance logic

After simulation, `plan_enrichment.py` audits the generated plan:

- ✓ 11-hour driving rule (per duty period)
- ✓ 14-hour duty window (per duty period)
- ✓ 30-minute break requirement
- ✓ 70-hour / 8-day cycle
- ✓ Required 10-hour resets

The **FMCSA Compliance Check** panel displays pass/fail for each rule with human-readable explanations.

## API response (key fields)

```json
{
  "route": { "total_distance_miles", "polyline", "stops" },
  "summary": { "total_days", "trip_start", "trip_end" },
  "logs": [ "per-calendar-day FMCSA log sheets" ],
  "compliance": { "compliant", "status", "checks" },
  "duty_periods": [ "per-period driving/on-duty/off-duty totals" ],
  "timeline": [ "chronological events with timestamps" ],
  "hos_explanations": [ "why each stop/reset was inserted" ],
  "stop_details": { "fuel_stops", "rest_stops" },
  "reviewer": { "raw metrics + assessment assumptions" }
}
```

## Assumptions (hardcoded per assessment)

| Assumption | Value |
|---|---|
| Driver type | Property-carrying (not passenger) |
| Cycle | 70-hour / 8-day (not 60/7) |
| Pickup / dropoff | 1 hour on-duty each |
| Fuel | Every 1,000 miles, 30-minute stop |
| Adverse weather | Not implemented |
| Sleeper berth split | Not implemented |
| Timezone | Single timezone (America/Chicago) |

## Tradeoffs

| Decision | Rationale |
|---|---|
| No database | Stateless request/response; no trip history required by assessment |
| Enrichment layer separate from HOS engine | Keeps simulation pure; explainability is derived, not mixed into core logic |
| Calendar-day log split at midnight | Matches FMCSA paper log format; requires duty-period panel to avoid reviewer confusion |
| OSRM/Nominatim fallback | Works without API keys for local demo; ORS optional for production |
| sessionStorage for results | Simple single-page flow; no auth or persistence needed |

## Tests

```bash
cd backend
python manage.py test tripplanner.tests
```

12 tests cover HOS engine edge cases, daily log 24-hour invariant, and enrichment/compliance audit.

## Deployment

- **Frontend (Vercel):** set `NEXT_PUBLIC_API_URL`
- **Backend (Render/Railway):** set `CORS_ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, optional `ORS_API_KEY`

## Screenshots

_Add screenshots of the results page showing Compliance Check, Duty Period Analysis, and Daily Log Sheets after deploying._

Recommended captures:
1. Trip input form
2. Results page — FMCSA Compliance Check (COMPLIANT)
3. Duty Period Analysis showing per-period driving ≤ 11h
4. Daily log sheet with midnight-split driving block
