# Architecture

```text
User
  |
  v
Next.js Web App
  |-- Intake UI
  |-- Lot Search / Map UI
  |-- Parcel Detail Page
  |-- Compliance Report
  |-- Schematic Tuning Chat
  |-- Visual Mockup / Walkthrough Viewer
  |-- Review Packet + Document Vault
  |
  v
FastAPI Backend
  |-- Auth/session checks
  |-- Project + parcel APIs
  |-- Listing search APIs
  |-- Compliance APIs
  |-- Design generation APIs
  |-- Document/export APIs
  |
  v
Agent Orchestrator
  |-- Intake Agent
  |-- Listing Agent
  |-- GIS Agent
  |-- Compliance Agent
  |-- Finance Agent
  |-- Design Agent
  |-- Visualization Agent
  |-- Review Packet Agent
  |
  v
Data + Integrations
  |-- Supabase Postgres + PostGIS
  |-- Supabase Storage / S3
  |-- Austin Open Data / Socrata
  |-- Austin ArcGIS FeatureServers
  |-- Licensed MLS/IDX or Apify prototype feed
  |-- Redfin Data Center market data
  |-- Mapbox / Google Street View / Nearmap
  |-- AutoHDR or image API fallback
```

## Design Boundary

LLMs may extract, explain, rank, summarize, and converse. Deterministic services own GIS joins, numeric calculations, compliance-rule execution, permissions, exports, and final status flags.

## Services

- `apps/web`: Next.js App Router frontend.
- `apps/api`: FastAPI backend.
- `packages/schemas`: shared JSON/Pydantic/Zod-facing contracts.
- `packages/rules`: deterministic compliance rules.
- `packages/integrations`: external API clients.
- `packages/agents`: OpenAI agent orchestration definitions.
- `packages/workers`: long-running jobs for ingestion, visuals, and exports.
