# Stage 1 Wireframe — Austin Build Feasibility AI

Polished interactive wireframe / prototype for the Stage 1 design review.

## What's here

A single-page React app (loaded via Babel standalone, no build step) that walks the
six-step feasibility workflow:

1. **Project intake** — structured spec + conversational request → validated contract
2. **Lot discovery** — ranked candidates from the prototype/static dataset
3. **Lot context** — selected parcel detail, source limitations, pending official joins
4. **Compliance feasibility** — advisory metrics table + Passes/Warnings/Unknowns/Fails
5. **Primary schematic plan** — one conceptual SVG floor plan with quality checks and a design-conversation queue
6. **Review packet** — per-reviewer document checklist (architect, civil, surveyor, attorney, city) with export actions

A Desktop / Mobile toggle in the top bar opens an iOS-frame mobile preview rendering the same workflow.

## Running

Open `index.html` directly in a browser — no build, no server required.

```bash
open wireframes/stage1/index.html
# or
python3 -m http.server -d wireframes/stage1 8080
```

## File layout

```
wireframes/stage1/
├── index.html          ← entry point
├── styles.css          ← design tokens + component CSS
├── data.js             ← mock data (lots, compliance rows, schematic, packet)
├── components.jsx      ← shared UI primitives (Btn, Panel, Status, Banner, JsonView, …)
├── app.jsx             ← top bar, left rail, workflow state machine, screen router
├── ios-frame.jsx       ← iPhone device frame for mobile preview
├── mobile.jsx          ← mobile renderings of each screen
└── screens/
    ├── intake.jsx
    ├── lots.jsx
    ├── lot-context.jsx
    ├── compliance.jsx
    ├── schematic.jsx
    └── packet.jsx
```

## Design system

- **Type:** Geist + Geist Mono (Google Fonts)
- **Background** `oklch(0.972 0.003 95)`, **panels** `#fff`, **borders** `oklch(0.91 0.005 90)`
- **Charcoal text** `oklch(0.22 0.012 240)`
- **Muted teal primary** `oklch(0.50 0.06 195)`
- **Status:** passes green `oklch(0.52 0.09 155)`, warning amber `oklch(0.62 0.13 75)`, fail red `oklch(0.55 0.16 25)`, unknown gray
- 6px radius, 1px borders, no gradients, no nested cards

## Notes & constraints

- Advisory feasibility only — not City of Austin approval; persistent disclaimer in the workspace footer.
- Lot data is labelled **prototype/static dataset · not current inventory** on every card.
- Schematic output is conceptual only — exactly one **Primary Feasibility Plan** per the spec.
- All async operations (Validate, Normalize, Find lots, Run feasibility, Generate plan) are simulated with `setTimeout`. Wire to the real API endpoints in Stage 2.

## Next steps

- Replace `data.js` mocks with `/listings/search`, `/listings/{id}/detail`, `/compliance/evaluate`, `/design/schematics` calls from the FastAPI backend.
- Replace map placeholder with the real Mapbox / aerial integration when the token is configured.
- Wire the design-conversation chips into the OpenAI revision loop.
- Add real upload endpoints behind the document-vault drop zones.
