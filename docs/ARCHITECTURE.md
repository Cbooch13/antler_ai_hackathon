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

## Stage 6E LLM Schematic Agent

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
  |-- Delegates schematic generation to OpenAISchematicDesignAgent
  |-- Uses OpenAI structured outputs when LLM_SCHEMATIC_ENABLED=true
  |-- Falls back to the local SchematicDesignAgent otherwise
  |-- Retrieves plan exemplars by property type, unit count, bedrooms, target sqft, and lot size
  |-- Adds research-reference guidance for ResPlan, RPLAN, Tell2Design, Graph2Plan, HouseLLM, DStruct2Design, and ZURU/AWS
  |-- Generates one primary human-comfort option from spec + property context
  |-- Locally generates seven exemplar-guided candidates and returns the best-scored plan
  |-- Reconciles room areas to the requested building square footage
  |-- Adds one dimensioned architectural concept plan to the option
  |-- Uses normalized rooms, walls, openings, scale assumptions, and SVG exports
  |-- Rejects synthetic path repair, bedroom access through other bedrooms, inefficient circulation, and implausible room-area balance
  |-- Carries forward warning/unknown/failing compliance findings
  |
  v
DesignGenerationResponse
```

Stage 6E is LLM-assisted, generative, and conceptual. It creates option cards, dimensioned architectural-style plan views, and downloadable SVG exports for review and later conversational tuning, but it does not create permit drawings, measured CAD/BIM files, AutoHDR imagery, or walkthrough assets.

## Stage 6F Floor-Plan Quality Validation

Stage 6F adds deterministic floor-plan quality reports to every generated plan. The current checker evaluates area reconciliation, footprint area, room bounds, room overlap, requested program fit, MVP room dimensions, circulation, openings, second-unit separation, and solar-orientation assumptions. These reports are returned in the API and rendered in the website so poor plans are visible instead of hidden behind an SVG.

This is the first tool layer for the agentic loop.

## Stage 6G Agentic Floor-Plan Revision Loop

Stage 6G adds the first correction loop around the OpenAI schematic planner. When OpenAI generation is enabled, the design service asks the model for structured layout JSON, converts it into floor plans, runs deterministic quality checks, and then returns failing/warning checks to the model for another attempt. The loop stops only when critical checks pass and the quality score is at least 85, or after `LLM_SCHEMATIC_MAX_ATTEMPTS` attempts. The default generation budget is seven. If no attempt meets the threshold, the service returns the highest-scoring advisory result with assumptions noting that unresolved warnings remain.

The local generator remains a single-pass fallback so the app can run without an API key.

## Stage 6H Structured Geometry Refiner

Stage 6H replaces the OpenAI path's equal-cell room placement with a category-aware geometry refiner. The refiner groups LLM-proposed rooms into public, circulation, private, wet-core, and unit zones, reconciles each room's displayed dimensions and area to the floor footprint, and generates interior wall lines from actual room boundaries. This produces more coherent SVG plans while preserving deterministic quality checks and the revision loop.

## Stage 6I Architectural Plan Renderer

Stage 6I changes the visual output from colored zoning blocks to an architectural-style SVG. The renderer uses a white plan background, wall line weights, door swings, window openings, room labels, and conceptual furniture/fixture symbols for beds, baths, kitchens, living rooms, laundry, and unit rooms. The website preview renders this generated SVG directly instead of rebuilding a colored block plan in React.

## Stage 6J Adjacency Graph And Circulation Solver

Stage 6J adds an explicit room-connection graph to every floor plan. Each connection records the source room, target room, connection type, normalized door/opening location, width, and orientation. The renderer uses these connections to draw interior doors/openings, and the quality checker now verifies that every room is reachable from the entry/circulation graph. This makes pathing a first-class contract rather than a decorative SVG detail.

## Stage 6K Dataset-Retrieved Plan Exemplars

Stage 6K adds the first retrieved-exemplar layer. The service maintains a small internal precedent library with plan families, room-area ratios, adjacency edges, aspect-ratio targets, and planning notes. These examples are research-cleared placeholders for the MVP; production datasets such as ResPlan, RPLAN, Tell2Design, or licensed internal plans still require license and commercial-use review before use.

The local generator now creates seven exemplar-guided candidates, runs deterministic quality and exemplar-fit checks, and returns only the highest-scoring primary plan. The OpenAI path includes the retrieved exemplars in the structured prompt and uses a default seven-generation revision budget before returning the first accepted plan or the best advisory plan.

## Stage 6L Research-Guided Plan Realism Constraints

Stage 6L adds research-reference guidance and stricter deterministic realism checks. The prompt includes method references for ResPlan, RPLAN, Tell2Design, Graph2Plan, HouseLLM, DStruct2Design, and ZURU/AWS so the LLM can follow the same planner/refiner/evaluator pattern, but the references are guidance only. The prompt explicitly asks for concise design assumptions and structured room data, not hidden chain-of-thought.

The checker now treats pathing and spacing as architectural constraints instead of cosmetic details:

- synthetic fallback path connections fail quality instead of silently making a room reachable
- bedrooms must connect directly to hall or entry circulation
- room-area balance flags implausibly large baths, bedrooms, services, entries, and unit rooms
- circulation efficiency must stay within MVP hallway/entry ratio assumptions
- wet rooms are checked for reasonable grouping

The LLM geometry refiner also inserts small wet-core support and private support rooms when a model underspecifies a compact plan, which prevents one bathroom or bedroom from absorbing all remaining square footage.

## Stage 6M Agentic Floor-Plan Pipeline

Stage 6M should continue replacing direct plan-shape generation with a structured planner/refiner/renderer pipeline. The core architectural decision is that LLMs reason over structured layout JSON and graph constraints, while deterministic code owns geometry, validation, and rendering.

```text
User brief + selected lot + compliance findings + sun/context metadata
  |
  v
LLM Planner Agent
  |-- Produces structured floor-plan JSON
  |-- Includes rooms, target areas, levels, adjacency graph, walls, openings, and constraints
  |-- Produces one primary human-comfort plan until the realism checks are strong enough for variants
  |
  v
Deterministic Constraint Tools
  |-- Area reconciliation and requested-square-foot utilization
  |-- Room minimums, proportions, and public/private zoning
  |-- Adjacency and circulation graph checks
  |-- Door reachability, exterior openings, and daylight/window checks
  |-- Multi-floor consistency and second-unit separation checks
  |-- Compliance-risk carry-forward checks
  |
  v
LLM Revision Loop
  |-- Receives constraint violations
  |-- Revises structured JSON until passing or marked infeasible/advisory
  |
  v
Geometry Refiner
  |-- Snaps walls to grid
  |-- Resolves overlaps and gaps
  |-- Converts adjacency graph into exact room geometry
  |-- Allocates levels and stair/service cores when needed
  |
  v
Deterministic Renderer
  |-- SVG plan export
  |-- Future DXF/Revit-compatible export
  |-- Future AutoHDR-ready scene package
```

The schema should represent the plan as inspectable data, not a generated image:

- `FloorPlanLevel`: level name, gross/net square footage, footprint dimensions, orientation, stair/service-core metadata
- `RoomNode`: type, target/actual square footage, dimensions, privacy zone, wet-room/daylight flags, user priority
- `AdjacencyEdge`: source room, target room, required/optional status, relationship type, and rationale
- `WallSegment`: start/end coordinates, thickness, interior/exterior/load-bearing assumption
- `Opening`: wall reference, type, width, sill/head metadata where available, and orientation
- `ConstraintReport`: violations, warnings, professional-review flags, and revision instructions

Dataset strategy:

- Use RPLAN and Tell2Design for research, prompt examples, and language-to-layout evaluation.
- Evaluate ResPlan for graph-native vector training/evaluation after license review.
- Track DStruct2Design and ZURU/AWS as references for structured representation and separate adherence/correctness evaluation.
- Do not ship research-dataset-derived training or examples into production until licenses and commercial-use rights are reviewed.

Evaluation must report instruction adherence separately from geometric correctness. Add architectural realism checks for circulation, room proportions, daylight, public/private zoning, wet-room grouping, second-unit access, and solar/window optimization. Fine-tuning remains a later option; prompt-only structured outputs plus deterministic validation are the required MVP path.
