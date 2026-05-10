# Floor Plan Generation Pause

Floor-plan generation is paused after Stage 6L. The current implementation should be treated as a useful scaffold for contracts, prompts, rendering, quality reports, and test coverage, but not as a product-quality architectural planner.

## Why It Is Paused

- The generated layouts can pass MVP heuristics while still feeling architecturally weak.
- Pathing, room spacing, door placement, and room proportions need stronger geometry logic than prompt tuning alone.
- Internal exemplar patterns help, but they are not a substitute for real plan datasets, a constraint solver, or a professional design engine.
- The current SVG renderer is useful for inspection, but visual plausibility should not be confused with architectural validity.

## Current State To Preserve

- One primary `human_comfort` schematic is returned.
- Local generation uses best-of-7 exemplar-guided candidates.
- OpenAI generation can use a seven-attempt revision loop when enabled.
- Research references are included as prompt guidance: ResPlan, RPLAN, Tell2Design, Graph2Plan, HouseLLM, DStruct2Design, and ZURU/AWS.
- Deterministic checks now cover path connectivity, bedroom privacy, circulation efficiency, room-area balance, wet-core grouping, exemplar fit, openings, and unit separation.
- Outputs remain conceptual and require architect, engineer, surveyor, attorney, and city review.

## Recommended Next Steps

1. Build a license-reviewed exemplar import pipeline.
   Convert owned or approved floor plans into the internal room graph, wall, opening, adjacency, room-ratio, and quality-check schema.

2. Replace rectangle packing with a real constraint/refinement layer.
   Use a deterministic solver for room placement, hall continuity, doors, minimum clearances, wet-wall grouping, stairs, windows, and exterior access.

3. Split planning into two explicit artifacts.
   First generate a room graph and adjacency/area program. Then generate geometry from that graph. Do not let the LLM directly own final geometry.

4. Add realism metrics before adding more visual polish.
   Track circulation ratio, room aspect ratios, door reachability, window access, wet-core distance, privacy zoning, exterior wall access, and similarity to exemplar distributions.

5. Consider external architecture tooling only after the schema stabilizes.
   Good candidates later may include CAD/BIM export tools, DXF/SVG geometry libraries, Speckle/IFC workflows, or a specialized floor-plan generation service if licensing and API quality are acceptable.

6. Keep generated plans advisory.
   Even after improvements, the product should present them as concept studies for professional review, not permit-ready architectural drawings.

## Resume Trigger

Resume this work when the product needs better schematic credibility and there is time to implement a real graph-to-geometry pipeline. The next planned stage is **Stage 6M - Real Dataset Exemplar Import Pipeline**.
