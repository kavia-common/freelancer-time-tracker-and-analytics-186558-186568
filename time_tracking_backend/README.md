# Time Tracking Backend

FastAPI backend for a freelancer time tracking application. Uses JSON files for storage (`time_tracking_backend/data/*.json`) until a database is configured.

- Projects: CRUD with optional default hourly rate
- Tasks: CRUD
- Sessions: CRUD with billable flag and hourly_rate override
- Analytics: daily/weekly/monthly totals and earnings
- Reports: PDF export scaffolding endpoint

## Run

Use uvicorn:

```
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

## Regenerate OpenAPI file

```
python -m src.api.generate_openapi
```

The generated JSON is written to `interfaces/openapi.json` for frontend consumption.
