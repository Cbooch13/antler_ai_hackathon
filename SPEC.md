# Specification

## Product Goal

Help a user evaluate Austin lots for a desired residential or commercial build, understand feasibility risks, create schematic concepts, generate conceptual visuals, and assemble a professional review packet.

## MVP Scope

Stage 2 establishes the system foundation, the first user-facing intake path, and official Austin public-data ingestion:

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
