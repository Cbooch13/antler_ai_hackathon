# Specification

## Product Goal

Help a user evaluate Austin lots for a desired residential or commercial build, understand feasibility risks, create schematic concepts, generate conceptual visuals, and assemble a professional review packet.

## MVP Scope

Stage 6J establishes the system foundation, the first user-facing intake path, official Austin public-data ingestion, MVP lot discovery, selected-lot context, advisory compliance feasibility, generative schematic-agent planning, conceptual architectural floor plans, deterministic floor-plan quality validation, OpenAI revision-loop feedback, structured geometry refinement, architectural plan rendering, and adjacency/circulation validation:

- Monorepo structure for web, API, workers, schemas, rules, integrations, and agents.
- Shared core data contracts.
- Deterministic compliance-rule boundary.
- API health endpoint.
- Documentation for architecture, environment variables, and stage gates.
- Initial tests for schema validity and rule output behavior.
- Typed intake form for Austin project specs.
- Conversational intake normalization endpoint with deterministic fallback parsing.
- Missing-field and lower-confidence commercial warnings.
- Austin Open Data/Socrata permit ingestion for `3syk-w9eu`.
- Austin ArcGIS zoning and TCAD parcel sample ingestion.
- Normalized public-data contracts with source URL, retrieval timestamp, confidence, license notes, and raw payload retention.
- Static Kaggle fallback listing adapter, explicitly marked as non-current prototype data.
- Lot ranking by budget fit, lot size fit, building size fit, bedroom fit, unit-count fit, and warning status.
- `/listings/search` API route and website button for prototype lot discovery.
- `/listings/{listing_id}/detail` API route for selected-lot context.
- Map context with coordinates, street-view link, optional aerial image URL, and missing-data warnings.
- Website lot-detail panel after selecting a ranked prototype lot.
- `/compliance/evaluate` API route for deterministic advisory feasibility findings.
- Website feasibility panel after selecting a lot and validated build spec.
- Explicit statuses for passes, warnings, unknowns, source limitations, and professional-review requirements.
- `/design/schematics` API route for one primary schematic option while plan quality is being tightened.
- Website schematic-options panel after compliance feasibility has been generated.
- At least one structured conceptual floor plan per schematic option.
- Website architectural-style plan views with rooms, dimensions, scale assumptions, walls, openings, room schedules, and SVG visual exports.
- Deterministic floor-plan quality reports covering area reconciliation, footprint fit, bounds, overlaps, program fit, room dimensions, circulation, openings, unit separation, and solar-orientation assumptions.
- OpenAI schematic revision loop that returns quality-check failures/warnings to the planner for up to `LLM_SCHEMATIC_MAX_ATTEMPTS` attempts, then accepts only plans with no critical-check failures and score `>= 85`, or returns the best advisory option set.
- Category-aware geometry refiner that places LLM-proposed rooms into public, circulation, private, wet-core, and unit zones before rendering.
- Interior wall generation from actual room boundaries instead of generic placeholder wall lines.
- Architectural SVG renderer with white plan background, wall line weights, smaller room labels, door arcs, windows, and conceptual fixture/furniture symbols.
- Explicit floor-plan connection graph with room-to-room edges, door/opening metadata, connection-derived interior door symbols, and path-connectivity checks that fail unreachable rooms.

## Source Priority

1. Official Austin GIS/Open Data and user-uploaded professional documents.
2. Licensed MLS/IDX feeds or approved listing providers.
3. MVP fallback datasets, clearly labeled as non-current prototype data. This includes the Kaggle Austin housing prices dataset at `https://www.kaggle.com/datasets/ericpierce/austinhousingprices` for static comps/workflow demos and Travis Central Appraisal District or Travis County public records/reports for parcel/property validation where legally and technically appropriate.
4. Prototype listing sources such as Apify, clearly labeled.
5. Inferred or LLM-produced summaries, always labeled with confidence and assumptions.

## Public Austin Data Ingestion

Stage 2 official-source ingestion includes:

- Austin issued construction permits through Socrata dataset `3syk-w9eu`.
- Austin zoning through `Publish_Zoning_AGOL/FeatureServer/0`.
- Austin TCAD parcel context through `EXTERNAL_tcad_parcel/FeatureServer/0`.

Every ingested record must preserve:

- source name and URL
- retrieval timestamp
- confidence level
- license/terms note when known
- raw response payload where useful for traceability
- warning text that city records should be professionally or officially verified before decisions

## MVP Listing Data Fallback

If MLS/IDX access is unavailable during the MVP, the system may use the Kaggle Austin housing prices dataset at `https://www.kaggle.com/datasets/ericpierce/austinhousingprices` as a static fixture source. These records must not be presented as active availability or live listings.

Fallback records must include:

- `source_mode = "prototype_static_dataset"`
- `current_inventory = false`
- dataset/source URL
- dataset year or retrieval timestamp when known
- license/terms metadata when known
- a user-facing note that the record is for demo, comp, ranking, or workflow validation only

Travis Central Appraisal District or Travis County records may be used to cross-reference parcel/property identity, address details, appraisal context, and ownership/property-record attributes where permitted. These records should not be treated as MLS/listing replacements.

## Lot Discovery Ranking

Stage 3 ranks candidate lot/listing records using deterministic scoring:

- budget fit
- target lot size fit
- target building size fit
- bedroom target fit
- unit-count target fit
- source/current-inventory warnings

Kaggle fallback rows must always return `current_inventory = false`, `source_mode = "prototype_static_dataset"`, and a prototype note. Licensed MLS/IDX sources are the only intended production path for live active listings.

## Parcel Detail and Map Context

Stage 4 selected-lot context must include:

- selected listing record
- prototype parcel shell when no official parcel id is available
- coordinates when available
- street-view URL when coordinates are available
- aerial/static-map URL only when a map provider token is configured
- explicit warnings for missing parcel id, zoning joins, permit joins, or imagery
- source metadata from the listing and public-data providers

Prototype detail views must not imply official parcel boundaries or city approval.

## Compliance Feasibility

Stage 5 compliance rules are deterministic and advisory. They may report:

- compliance table values for lot information, zoning, setbacks, building coverage, environmental overlays, crime statistics, and permit history
- static dataset limitations
- lot-size target fit
- unit-count target fit
- missing official zoning joins
- tree review unknowns
- floodplain/WUI overlay unknowns
- commercial MVP scope limitations

Compliance results must never imply permit approval. Every finding must include a status, confidence level, professional-verification flag, and citations/source metadata where available.

Metrics whose data has not been integrated must be shown as `Unknown` with a reason, not omitted.

## Schematic Options

Stage 6J schematic options are generative planning outputs generated by the Schematic Design Agent from the selected lot, validated build spec, property context, and compliance findings. When `LLM_SCHEMATIC_ENABLED=true` and `OPENAI_API_KEY` is configured, the Design Agent uses OpenAI structured outputs; otherwise it uses the local generator fallback. The service returns:

- one primary human-comfort option
- target building square footage
- unit count
- assumptions
- floor plans with rooms, dimensions, estimated square footage, scale assumptions, normalized layout coordinates, walls, openings, SVG visual exports, and notes
- quality reports with check-level status, score, and professional-review notes
- OpenAI revision-loop assumptions showing which attempt met the `>= 85` quality threshold or whether the best available advisory result was returned
- carried-forward compliance findings
- warnings that outputs are conceptual and require professional review

Floor plans are generated concept plans for early product review. The LLM or local generator must reconcile room square footage to the requested building square footage and should follow basic architectural planning practices such as public/private zoning, grouped wet rooms, circulation control, exterior openings, and separated second-unit access where relevant. They are not measured architectural drawings and do not validate egress, MEP, structural, accessibility, fire, or permit requirements.

Stage 6 does not generate permit-ready architectural drawings, CAD files, renderings, AutoHDR assets, or walkthroughs.

## Agentic Floor-Plan Roadmap

Stage 6F will move schematic generation toward an agentic, research-backed floor-plan pipeline. The Design Agent should not generate images first. It should generate a structured floor-plan representation that deterministic geometry and validation code can inspect.

The structured representation must include:

- room nodes with type, target square footage, actual square footage, minimum dimensions, privacy zone, wet-room flag, daylight/window needs, and user-requested priority
- adjacency graph edges with relationship type, required/optional status, and rationale
- level metadata for single-story, multi-story, ADU, and multi-unit plans
- wall segments as coordinate pairs with wall type and thickness
- doors and windows as references to wall segments, with swing/size/orientation metadata where available
- building-envelope, setback, sun-orientation, circulation, egress-review, and professional-review metadata

The agentic pipeline should use a three-stage pattern:

1. LLM Planner Agent: interpret the natural-language brief, property context, sun orientation, compliance findings, and style goals into structured layout JSON.
2. Geometry Refinement: convert the layout graph into exact geometry, snap walls to a grid, resolve overlaps, size hallways/rooms, allocate multiple floors, and ensure all requested square footage is accounted for.
3. Deterministic Rendering: render final geometry to SVG first, then later DXF/Revit-compatible or AutoHDR-ready exports.

The agent loop must call deterministic tools rather than asking the LLM to guess validity:

- constraint checker for area reconciliation, minimum room dimensions, overlapping geometry, wall alignment, door reachability, room connectivity, hallway width, exterior-window access, and second-unit separation
- compliance checker for carried-forward zoning, setback, coverage, tree, floodplain, WUI, and permit-risk findings
- solar/context checker for street orientation, likely west/east heat gain, south-facing glazing opportunities, shaded outdoor space, and window-placement recommendations
- revision loop that returns tool violations to the LLM Planner Agent until the plan passes MVP checks or is marked as infeasible/advisory

Reference datasets for research and evaluation:

- RPLAN: large public residential floor-plan dataset with roughly 80k annotated plans, useful for baseline layout patterns and raster-to-structure experiments.
- ResPlan: 2025 dataset of 17,000 vector/graph residential plans with room connectivity and geometry-cleaning pipeline; candidate source for graph-native spatial reasoning, subject to license review (`https://www.kaggle.com/datasets/resplan/resplan`).
- Tell2Design: ACL 2023 dataset pairing 80k+ floor-plan designs with natural-language instructions, useful for instruction-adherence evaluation and language-to-layout prompting (`https://aclanthology.org/2023.acl-long.820/`).
- DStruct2Design: data-structure-driven floor-plan benchmark using JSON-style floor-plan metadata, numerical constraints, and graph constraints; useful for the internal schema and evaluation style (`https://arxiv.org/abs/2407.15723`).
- ZURU/AWS text-to-floor-plan case study: useful precedent for evaluating instruction adherence and mathematical/geometric correctness separately (`https://aws.amazon.com/blogs/machine-learning/how-zuru-improved-the-accuracy-of-floor-plan-generation-by-109-using-amazon-bedrock-and-amazon-sagemaker/`).

Evaluation must use separate metrics for:

- instruction adherence: requested room counts, room types, units, adjacencies, style goals, privacy separation, and user edits
- mathematical/geometric correctness: positive room areas, total square-foot reconciliation, non-overlap, wall alignment, reachable doors, connected circulation, valid exterior openings, and multi-floor consistency
- architectural realism: circulation efficiency, room proportion checks, public/private zoning, wet-room stacking/grouping, daylight access, solar exposure, and similarity to real plan distributions

Fine-tuning is not required for the MVP. Prompting with structured outputs, retrieval examples, and deterministic validation should come first. Fine-tuning should only be considered after the schema, constraint checker, dataset license review, and evaluation harness are stable. If fine-tuning is pursued, compare prompt-only, LoRA, and full fine-tuning against the same adherence and correctness metrics before adopting the extra infrastructure cost.

## Agent Responsibilities

- Intake Agent: convert natural language into a structured build spec.
- Listing Agent: find candidate lots from approved listing sources.
- GIS Agent: join candidates to parcel, zoning, permit, and overlay data.
- Compliance Agent: explain deterministic rule outputs and missing data.
- Finance Agent: estimate feasibility economics.
- Design Agent: create schematic options constrained by compliance findings.
- Visualization Agent: generate conceptual visual assets.
- Review Packet Agent: assemble checklists, documents, citations, and exports.

## Non-Goals

- No production MLS scraping.
- No presentation of Kaggle/static fallback rows as active listings.
- No representation that feasibility output is permit approval.
- No LLM-owned final compliance status.
- No commercial code-path confidence parity until commercial rules are modeled.

## Stage Review Rule

Each stage must stop after implementation, verification, and a stage-specific git commit for human review before the next stage begins.
