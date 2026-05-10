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

## Stage 2 Public Data

The Stage 2 ingestion path is backend-first:

```text
FastAPI /data/austin/*
  |
  v
Data ingestion service
  |
  |-- SocrataPermitClient -> Austin issued construction permits
  |-- ArcGisFeatureLayerClient -> zoning FeatureServer
  |-- ArcGisFeatureLayerClient -> TCAD parcel FeatureServer
  |
  v
Normalized PermitRecord / GisFeatureRecord with SourceMetadata
```

Stage 2 does not persist records yet. Persistence, spatial joins, stale-data policy, and scheduled workers are deferred to later stages.

## Stage 3 Lot Discovery

```text
Next.js Intake UI
  |
  v
POST /listings/search
  |
  v
Listing service
  |
  |-- Static Kaggle fixture adapter for MVP fallback
  |-- Future licensed MLS/IDX adapter
  |
  v
Deterministic ranking
  |
  v
LotSearchResponse with currentInventory=false for prototype rows
```

Stage 3 intentionally does not scrape live listing websites. Static fallback rows are used for demos and workflow validation only.

## Stage 4 Parcel Detail

```text
Ranked lot card
  |
  v
GET /listings/{listing_id}/detail
  |
  v
Parcel detail service
  |
  |-- Static listing fixture
  |-- Prototype parcel shell
  |-- MapContext with coordinates and street-view URL
  |-- Future zoning/permit/parcel spatial joins
  |
  v
ParcelDetailResponse with explicit missing-data warnings
```

Stage 4 does not claim official parcel boundaries. It exposes context and warnings so later compliance stages can add deterministic checks safely.

## Stage 5 Compliance

```text
Selected lot + validated UserBuildSpec
  |
  v
POST /compliance/evaluate
  |
  v
Compliance service
  |
  |-- Load selected lot context
  |-- Run deterministic rules
  |-- Build compliance metrics table
  |-- Preserve citations/source metadata
  |
  v
ComplianceEvaluationResponse
```

The LLM does not own final compliance status. Stage 5 findings are deterministic and explicitly advisory until official zoning, parcel, tree, floodplain, WUI, survey, and permit-review data are joined.

## Stage 6C Schematic Agent

```text
Compliance feasibility + selected lot + validated UserBuildSpec
  |
  v
POST /design/schematics
  |
  v
Design service
  |
  |-- Reuses deterministic compliance response
  |-- Delegates schematic generation to SchematicDesignAgent
  |-- Creates human-comfort and space-utilization options
  |-- Adds one architectural concept plan to each option
  |-- Uses normalized rooms, walls, and openings for SVG plan rendering
  |-- Carries forward warning/unknown/failing compliance findings
  |
  v
DesignGenerationResponse
```

Stage 6C is still deterministic and conceptual. It creates option cards and architectural-style plan views for review and later conversational tuning, but it does not create permit drawings, measured CAD/BIM files, AutoHDR imagery, or walkthrough assets.
