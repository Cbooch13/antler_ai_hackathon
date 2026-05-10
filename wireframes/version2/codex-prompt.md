# Codex handoff prompt

Paste this into Codex (or a similar coding agent) along with the project files.

---

You are picking up a static React + Babel prototype of **Austin Build Feasibility AI** and turning it into a real Vite + React + TypeScript app. The prototype is locked-in UX — your job is to preserve every screen, interaction, and copy decision while migrating to a production stack.

**Read `AGENTS.md` first.** It explains the architecture, the workflow state machine, the data shapes, and the constraints you must not regress.

## Goal of this first batch of work

1. Scaffold a Vite + React + TypeScript project at the repo root (or `web/` — your call, document it).
2. Generate TypeScript types from the `data.js` shapes. Put them in `src/types.ts`.
3. Port `components.jsx` → `src/components/` as `.tsx` files. One file per component. Match the existing className API exactly so the CSS keeps working.
4. Port `styles-v2.css` (the v2 / editorial aesthetic is canonical) into a global stylesheet — keep the CSS custom properties intact for now, we'll move to Tailwind theme tokens in a later PR.
5. Port the six screens from `screens/*-v2.jsx` and `screens/*.jsx` (use v2 versions where they exist; the others apply to both). Wire them through `react-router-dom` with one route per workflow step.
6. Recreate the workflow state machine from `app-v2.jsx`. Keep the same job names (`validate`, `normalize`, `findLots`, `feasibility`, `plan`) so Stage 3 can swap mocks for real API calls without renaming anything.
7. Recreate the landing screen from `landing.jsx` at `/`. Workspace lives at `/workspace/:step?`.
8. Stub `src/api/` with one function per job; have each return a Promise that resolves with the corresponding mock object from `data.js` after a realistic delay.

## Constraints (from AGENTS.md — do not regress)

- Persistent advisory disclaimer on every workspace screen
- Every lot tagged `prototype · static dataset · not current inventory`
- One primary schematic plan only — never "options"
- Compliance table keeps every column: category, metric, value, basis, status, confidence, notes
- Locked-step gating: cannot jump past `state.step`
- Mobile preview is reachable via the Desktop/Mobile toggle in the top bar

## Out of scope for this PR

- Real auth, persistence, uploads, Mapbox, LLM calls, MLS — those are Stage 3+
- Visual redesign — match the v2 prototype pixel-by-pixel
- Tests beyond a Playwright smoke test that walks the six steps end-to-end

## Done means

- `npm run dev` boots the app at http://localhost:5173
- Navigating from the landing page to each of the six workspace screens produces the same content as the v2 prototype
- The Mobile toggle still works
- `tsc --noEmit` is clean
- Lighthouse Accessibility ≥ 95 on the workspace
