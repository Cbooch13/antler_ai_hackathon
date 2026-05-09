# Austin Build Feasibility AI

A staged hackathon MVP for an Austin real estate feasibility and design assistant.

The system combines:

- Next.js web UI for intake, lot review, map context, schematic tuning, visuals, and review packets.
- FastAPI backend for projects, parcels, compliance, documents, and agent orchestration.
- Supabase/Postgres/PostGIS-ready data contracts for parcels, listings, GIS joins, and document storage.
- Deterministic compliance rules separated from LLM reasoning.
- OpenAI agent placeholders for intake, listing, GIS, compliance, finance, design, visualization, and review-packet workflows.

## Stage Gate

Current implementation target: **Stage 1 - User Spec Intake**.

Stage 1 provides the repository structure, architecture/spec docs, shared schemas, API health route, deterministic rule stub, env template, typed intake form, normalization endpoint, and intake tests. Future stages should be implemented only after review.

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

## Important Disclaimer

This product provides feasibility and design decision support. It is not official City of Austin approval and is not a substitute for review by an architect, civil engineer, surveyor, attorney, arborist, or city official.
