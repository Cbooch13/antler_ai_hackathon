# Austin Build Feasibility AI

A staged hackathon MVP for an Austin real estate feasibility and design assistant.

The system combines:

- Next.js web UI for intake, lot review, map context, schematic tuning, visuals, and review packets.
- FastAPI backend for projects, parcels, compliance, documents, and agent orchestration.
- Supabase/Postgres/PostGIS-ready data contracts for parcels, listings, GIS joins, and document storage.
- Deterministic compliance rules separated from LLM reasoning.
- OpenAI agent placeholders for intake, listing, GIS, compliance, finance, design, visualization, and review-packet workflows.

## Stage Gate

Current implementation target: **Stage 5 - Compliance Feasibility Engine**.

Stage 5 provides the repository structure, architecture/spec docs, shared schemas, API health route, deterministic compliance rules, env template, typed intake form, normalization endpoint, Austin Socrata/ArcGIS ingestion clients, normalized permit/GIS records, static MVP listing fallback, lot ranking, selected-lot context, map links, advisory compliance feasibility checks, a compliance metrics table, and tests. Future stages should be implemented only after review.

Each stage must end with:

1. Verification commands passing.
2. A review checkpoint.
3. A git commit for the completed stage.

## Local Checks

Python checks available in this environment:

```bash
python3 -m pytest
```

Frontend checks require Node/pnpm:

```bash
pnpm install
pnpm --filter web test
pnpm --filter web typecheck
pnpm --filter web lint
pnpm --filter web build
```

Run the FastAPI server from the monorepo root:

```bash
PYTHONPATH=apps/api:packages/schemas/python:packages/rules/python:packages/integrations/python:packages/agents/python:packages/workers/python .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the Next.js app:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 pnpm --filter web dev --hostname 127.0.0.1 --port 3000
```

Stage 2 public-data endpoints:

```bash
curl "http://127.0.0.1:8000/data/austin/permits/recent?limit=5"
curl "http://127.0.0.1:8000/data/austin/zoning/sample?limit=5"
curl "http://127.0.0.1:8000/data/austin/parcels/sample?limit=5"
```

Stage 3 lot discovery endpoint:

```bash
curl -X POST "http://127.0.0.1:8000/listings/search" \
  -H "Content-Type: application/json" \
  -d '{"spec":{"projectName":"ADU search","city":"Austin","state":"TX","propertyType":"adu","totalBudgetUsd":850000,"targetLotSqft":6500,"targetBuildingSqft":2200,"bedrooms":4,"bathrooms":3,"units":2,"stylePreferences":[],"riskTolerance":"medium"},"sourceMode":"prototype_static_dataset","limit":5}'
```

Stage 4 parcel detail endpoint:

```bash
curl "http://127.0.0.1:8000/listings/kaggle-austin-001/detail"
```

Stage 5 compliance endpoint:

```bash
curl -X POST "http://127.0.0.1:8000/compliance/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"spec":{"projectName":"ADU search","city":"Austin","state":"TX","propertyType":"adu","totalBudgetUsd":850000,"targetLotSqft":6500,"targetBuildingSqft":2200,"bedrooms":4,"bathrooms":3,"units":2,"stylePreferences":[],"riskTolerance":"medium"},"listingId":"kaggle-austin-001"}'
```

## Important Disclaimer

This product provides feasibility and design decision support. It is not official City of Austin approval and is not a substitute for review by an architect, civil engineer, surveyor, attorney, arborist, or city official.
