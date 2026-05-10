# AGENTS.md — Austin Build Feasibility AI prototype

This repo contains a static, no-build interactive wireframe for the **Austin Build Feasibility AI** workspace. It exists to (a) lock the UX shape with stakeholders and (b) give the engineering team a concrete frontend to wire to real services in Stage 2.

You (Codex) are picking this up to turn the prototype into a real app. Read this whole file before making changes.

## What's in the box

```
.
├── Austin Build Feasibility AI.html       ← v1 (operational SaaS, original)
├── Austin Build Feasibility AI v2.html    ← v2 (editorial / Apple aesthetic + landing)
├── styles.css            v1 design tokens
├── styles-v2.css         v2 design tokens
├── photos.js             Unsplash placeholder photo URLs (REPLACE before prod)
├── data.js               Mock data: project, intake, lots, compliance, schematic, packet
├── components.jsx        Shared primitives: Icon, Btn, Status, Banner, Panel, JsonView, LockedState, Skel, fmt
├── ios-frame.jsx         iPhone device shell for mobile preview
├── app.jsx               v1 app shell (top bar, left rail, workflow state machine)
├── app-v2.jsx            v2 app shell (adds landing → workspace router, swaps lot screens)
├── landing.jsx           v2 landing screen (hero, workflow grid, intake-launch CTA)
├── mobile.jsx            Mobile renderings of all six screens
└── screens/
    ├── intake.jsx           Project intake + Validated Contract panel
    ├── lots.jsx             Lot Discovery (v1 placeholder thumbs)
    ├── lots-v2.jsx          Lot Discovery (image-led cards)
    ├── lot-context.jsx      Lot Context (v1)
    ├── lot-context-v2.jsx   Lot Context (v2 photo aerial)
    ├── compliance.jsx       Compliance metrics table + findings
    ├── schematic.jsx        Primary Feasibility Plan + quality checks + design conversation
    └── packet.jsx           Reviewer-by-reviewer document checklist
```

## Stack

- **Plain HTML + React 18 UMD + Babel Standalone**, loaded via `<script>` tags. No bundler, no npm, no build step.
- Runs by opening the HTML file directly, or `python3 -m http.server`.
- Cross-script scope: each `<script type="text/babel">` gets its own scope. Components are exposed via `window.X = X` at the bottom of each file.

**For production:** convert to Vite + React + TS. Architecture below maps cleanly.

## Architecture

### Workflow state machine
Single source of truth in `app-v2.jsx` (or `app.jsx`):
```js
state = {
  screen,            // 'intake' | 'lots' | 'lot-context' | 'compliance' | 'schematic' | 'packet'
  step,              // 1-6, gates the left rail
  validated,         // Intake contract validated
  selectedLotId,     // null until user picks a lot
  intake, conversation,
}
```
Steps lock until `step >= STEPS[i].needs + 1`. Async stages (`validate`, `normalize`, `findLots`, `feasibility`, `plan`) are simulated via `setTimeout` in `run(job)`. **Replace `run` with real API calls** — the rest of the state machine stays.

### Design system
- Type: Geist + Geist Mono + Instrument Serif (v2 only)
- Tokens are CSS custom properties in `:root` of each stylesheet. **Migrate these to a Tailwind config or CSS-in-JS theme.**
- Status semantics: `passes` / `warning` / `unknown` / `fail` / `info` — use these everywhere, not raw colors.
- Radius 6–10px, 1px borders, no gradients, no nested cards.

### Data shapes (in `data.js`)
- `project` — project header
- `intakeDefaults` — initial form state
- `validatedContract` — what the contract panel renders
- `lots[]` — id, address, city, neighborhood, price, lotSqft, buildingSqft, beds/baths/units, score, coords, reasons[]
- `compliance.rows[]` — { category, metric, value, basis, status, confidence, notes }
- `compliance.findingsGrouped` — { passes, warnings, unknowns, fails } each with { title, body }
- `schematic` — { name, targetSqft, units, qualityScore, qualityStatus, rooms[], qualityChecks[], revisionNotes[] }
- `packet.groups[]` — { role, status, notes, documents[] }

These shapes match the FastAPI backend the team is building. Lock them, generate TypeScript types from them, then wire endpoints.

## Endpoints to wire (Stage 2)

| Action in `run(job)` | Endpoint to wire |
|---|---|
| `validate`     | local form validation, no API |
| `normalize`    | `POST /intake/normalize` (LLM normalize free-text request → spec) |
| `findLots`     | `POST /listings/search` (search prototype dataset until MLS ingest) |
| `feasibility`  | `POST /compliance/evaluate` (runs zoning/setback/coverage/env checks) |
| `plan`         | `POST /design/schematics` (LLM + deterministic quality checker loop) |

Replace the mock photos in `photos.js` with `/listings/{id}/photos` once the backend serves them. Replace `map-placeholder` aerial backgrounds with Mapbox tiles when the token is configured.

## Constraints — do not regress

- **Advisory feasibility only** — every screen carries the disclaimer; do not remove.
- **Static dataset labelling** — every lot card / lot context view tags rows as `prototype · static dataset · not current inventory`. Keep this until live MLS is wired.
- **Apify must not appear** in copy or code.
- **One primary schematic plan** — not "schematic options". Any future N-options work needs a separate UX review.
- **Locked-step gating** — never let a user jump past a step that's not complete; show `LockedState`.
- **Confidence + basis on every compliance row** — don't drop columns.

## Suggested first PR for Codex

1. `npm create vite@latest` → React + TS template
2. Port `data.js` → `src/data/mock.ts` with TS types matching the shapes above
3. Port `components.jsx` → `src/components/*.tsx`
4. Port screens 1:1 — start with v2 (`Austin Build Feasibility AI v2.html` is the canonical aesthetic)
5. Wire `app-v2.jsx`'s state machine into `src/App.tsx` with `react-router` for screen routes
6. Move CSS variables in `styles-v2.css` into Tailwind theme tokens (or keep as-is in a global stylesheet)
7. Stub the API client in `src/api/` — same function names as `run(job)` cases above
8. Replace mock `setTimeout` calls with real `fetch` once endpoints exist

Tests are out of scope for the prototype. Add Playwright smoke tests for the six-step flow when porting.

## Things explicitly NOT done in the prototype

- No real auth
- No persistence — state lives in memory only
- No real upload — `upload-zone` divs are visual only
- No real Mapbox / aerial imagery (placeholder photos)
- No real LLM normalization (mock contract in `data.js`)
- Mobile view is a preview iframe inside the desktop shell, not a separate route

Ship those in Stage 2.
