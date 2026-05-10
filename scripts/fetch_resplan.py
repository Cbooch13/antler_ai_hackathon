#!/usr/bin/env python3
"""
Fetch the ResPlan dataset from GitHub, render PNG thumbnails, and write
apps/web/public/floorplans/index.json for the Austin Build Feasibility app.

Requirements (install once):
    pip install shapely matplotlib numpy tqdm

Usage:
    python scripts/fetch_resplan.py [--limit 60] [--out apps/web/public/floorplans]
"""

import argparse
import json
import math
import os
import pickle
import sys
import zipfile
from pathlib import Path
from typing import Any



# ── colour palette (matches the existing SVG floor plan in SchematicScreen) ──
ROOM_COLOURS: dict[str, str] = {
    "bedroom":    "#d4edda",  # soft green
    "bathroom":   "#cce5ff",  # soft blue
    "kitchen":    "#fff3cd",  # soft amber
    "inner":      "#e2f0fb",  # teal-ish (living / dining)
    "balcony":    "#f8f9fa",  # near-white
    "veranda":    "#f8f9fa",
    "garden":     "#d4edda",
    "storage":    "#f0e6f6",  # lavender
    "parking":    "#e9ecef",
    "stair":      "#dee2e6",
    "land":       "#ffffff",
    "wall":       "#333333",
}

LICENSE_NOTE = "ResPlan academic dataset — license review required before production use."


# ─────────────────────────────────────────────────────────────────────────────
# Download
# ─────────────────────────────────────────────────────────────────────────────

GITHUB_ZIP_URL = "https://raw.githubusercontent.com/m-agour/ResPlan/main/ResPlan.zip"


def download_dataset(dest_dir: Path) -> Path:
    """Download and extract ResPlan.zip from GitHub, return path to .pkl."""
    import urllib.request

    dest_dir.mkdir(parents=True, exist_ok=True)

    existing = list(dest_dir.rglob("*.pkl"))
    if existing:
        print(f"Found cached pickle: {existing[0]}")
        return existing[0]

    zip_path = dest_dir / "ResPlan.zip"
    print(f"Downloading ResPlan.zip from GitHub (~100 MB)…")

    def _progress(block_count: int, block_size: int, total: int) -> None:
        done = block_count * block_size
        pct  = min(100, int(done / total * 100)) if total > 0 else 0
        mb   = done / 1_048_576
        print(f"\r  {pct}%  ({mb:.1f} MB)", end="", flush=True)

    urllib.request.urlretrieve(GITHUB_ZIP_URL, zip_path, reporthook=_progress)
    print()

    print("Extracting…")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    zip_path.unlink()

    pkls = list(dest_dir.rglob("*.pkl"))
    if not pkls:
        print("[ERROR] No .pkl file found after extraction.")
        sys.exit(1)

    print(f"Pickle located: {pkls[0]}")
    return pkls[0]


# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────

def iter_geoms(geom: Any):
    """Yield individual Shapely geometries from single/multi/collection."""
    from shapely.geometry.base import BaseGeometry
    if geom is None:
        return
    if isinstance(geom, (list, tuple)):
        for item in geom:
            yield from iter_geoms(item)
    elif not isinstance(geom, BaseGeometry):
        return  # skip scalars like wall_depth (float), id (int), etc.
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:
            yield from iter_geoms(g)
    else:
        yield geom


def count_parts(geom: Any) -> int:
    return sum(1 for _ in iter_geoms(geom))


def geom_area(geom: Any) -> float:
    if geom is None:
        return 0.0
    return sum(g.area for g in iter_geoms(geom) if hasattr(g, "area"))


def plan_bounds(plan: dict) -> tuple[float, float, float, float]:
    """Return (minx, miny, maxx, maxy) across all geometries in the plan."""
    from shapely.geometry import box
    all_geoms = []
    for key, val in plan.items():
        if key in ("id", "unitType", "area", "net_area"):
            continue
        for g in iter_geoms(val):
            all_geoms.append(g)
    if not all_geoms:
        return (0, 0, 1, 1)
    from shapely.ops import unary_union
    union = unary_union(all_geoms)
    return union.bounds  # minx, miny, maxx, maxy


# ─────────────────────────────────────────────────────────────────────────────
# Rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_plan_png(plan: dict, out_path: Path, dpi: int = 120) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection

    fig, ax = plt.subplots(figsize=(6, 5), dpi=dpi)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#fafafa")

    minx, miny, maxx, maxy = plan_bounds(plan)
    pad = (maxx - minx) * 0.04
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)

    def add_polys(key: str, colour: str, edge: str = "#cccccc", lw: float = 0.4, z: int = 2) -> None:
        geom = plan.get(key)
        if geom is None:
            return
        patches = []
        for g in iter_geoms(geom):
            if not hasattr(g, "exterior"):
                continue
            xy = [(c[0], c[1]) for c in g.exterior.coords]
            patches.append(MplPolygon(xy, closed=True))
        if patches:
            pc = PatchCollection(patches, facecolor=colour, edgecolor=edge,
                                 linewidth=lw, zorder=z)
            ax.add_collection(pc)

    # Draw filled rooms back-to-front; walls/doors are Polygons too in this dataset
    add_polys("land",       ROOM_COLOURS["land"],    z=1)
    add_polys("inner",      ROOM_COLOURS["inner"],   z=2)
    add_polys("living",     ROOM_COLOURS["inner"],   z=2)
    add_polys("bedroom",    ROOM_COLOURS["bedroom"], z=2)
    add_polys("bathroom",   ROOM_COLOURS["bathroom"],z=2)
    add_polys("kitchen",    ROOM_COLOURS["kitchen"], z=2)
    add_polys("balcony",    ROOM_COLOURS["balcony"], z=2)
    add_polys("veranda",    ROOM_COLOURS["veranda"], z=2)
    add_polys("garden",     ROOM_COLOURS["garden"],  z=2)
    add_polys("storage",    ROOM_COLOURS["storage"], z=2)
    add_polys("parking",    ROOM_COLOURS["parking"], z=2)
    add_polys("stair",      ROOM_COLOURS["stair"],   z=2)
    add_polys("wall",       "#333333", "#333333", lw=0, z=3)
    add_polys("door",       "#aaaaaa", "#aaaaaa", lw=0, z=4)
    add_polys("front_door", "#c0392b", "#c0392b", lw=0, z=5)

    # North arrow (top-right corner)
    ax.annotate("N", xy=(maxx - pad * 0.5, maxy - pad * 0.5),
                fontsize=8, ha="center", va="center",
                fontfamily="monospace", color="#555555", zorder=7)

    plt.tight_layout(pad=0.2)
    fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Metadata extraction
# ─────────────────────────────────────────────────────────────────────────────

STYLE_BY_ROOM: list[tuple[str, str]] = [
    ("balcony",  "outdoor living"),
    ("garden",   "garden"),
    ("veranda",  "outdoor living"),
    ("parking",  "with parking"),
]


def infer_style_keywords(plan: dict, beds: int, sqft: int) -> list[str]:
    keywords: list[str] = []
    for key, label in STYLE_BY_ROOM:
        if plan.get(key) is not None:
            keywords.append(label)
    if sqft > 2500:
        keywords.append("spacious")
    elif sqft < 1000:
        keywords.append("compact")
    if beds >= 4:
        keywords.append("family")
    if not keywords:
        keywords.append("warm modern")
    return keywords


def infer_family(beds: int, units: int) -> str:
    if units >= 2:
        return "stacked-duplex" if beds >= 4 else "rear-adu"
    if beds <= 2:
        return "side-hall"
    return "central-hall"


def infer_property_types(beds: int, units: int) -> list[str]:
    if units >= 3:
        return ["Small multifamily"]
    if units == 2:
        return ["Duplex", "ADU"]
    if beds <= 1:
        return ["ADU"]
    if beds <= 3:
        return ["Single-family residence", "ADU"]
    return ["Single-family residence"]


SQM_TO_SQFT = 10.7639


def extract_entry(plan: dict, image_url: str) -> dict:
    plan_id = str(plan.get("id", "unknown"))

    # Room counts
    beds   = count_parts(plan.get("bedroom"))
    baths  = count_parts(plan.get("bathroom"))
    units  = int(plan.get("unitType", 1) or 1)

    # Area: prefer explicit field, fall back to summing bedroom + inner areas
    raw_area = plan.get("net_area") or plan.get("area")
    if raw_area and float(raw_area) > 0:
        # Determine if the value is already sqft or sqm by magnitude
        raw = float(raw_area)
        sqft = int(raw * SQM_TO_SQFT) if raw < 600 else int(raw)
    else:
        inner_area = geom_area(plan.get("inner"))
        bedroom_area = geom_area(plan.get("bedroom"))
        raw_sqm = inner_area + bedroom_area
        sqft = int(raw_sqm * SQM_TO_SQFT) if raw_sqm > 0 else beds * 380 + 500

    sqft = max(400, min(sqft, 8000))  # sanity clamp

    # Room type list (labels for frontend chips)
    room_types: list[str] = []
    for key in ("bedroom", "bathroom", "kitchen", "inner", "balcony",
                "veranda", "garden", "storage", "parking", "stair"):
        n = count_parts(plan.get(key))
        room_types.extend([key] * n)

    return {
        "id":            f"resplan-{plan_id}",
        "name":          f"ResPlan #{plan_id} — {beds}bd/{baths}ba",
        "family":        infer_family(beds, units),
        "beds":          beds,
        "baths":         baths,
        "units":         units,
        "sqftEstimate":  sqft,
        "sqftRange":     [int(sqft * 0.85), int(sqft * 1.15)],
        "propertyTypes": infer_property_types(beds, units),
        "styleKeywords": infer_style_keywords(plan, beds, sqft),
        "roomTypes":     room_types,
        "imageUrl":      image_url,
        "sourceDataset": "ResPlan",
        "licenseNote":   LICENSE_NOTE,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch & index ResPlan dataset.")
    parser.add_argument("--limit", type=int, default=60,
                        help="Max number of plans to export (default: 60)")
    parser.add_argument("--out", default="apps/web/public/floorplans",
                        help="Output directory for PNGs + index.json")
    parser.add_argument("--cache", default=".resplan_cache",
                        help="Directory to cache the downloaded dataset")
    parser.add_argument("--skip-render", action="store_true",
                        help="Skip PNG rendering (useful for re-running metadata only)")
    args = parser.parse_args()

    cache_dir = Path(args.cache)
    out_dir   = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Download ──────────────────────────────────────────────────────────
    pkl_path = download_dataset(cache_dir)

    # ── 2. Load ──────────────────────────────────────────────────────────────
    print(f"Loading pickle ({pkl_path.stat().st_size // 1_048_576} MB)…")
    with open(pkl_path, "rb") as f:
        plans: list[dict] = pickle.load(f)
    print(f"Loaded {len(plans):,} floor plans.")

    # ── 3. Filter: skip plans with no usable geometry ────────────────────────
    usable = [p for p in plans
              if count_parts(p.get("bedroom")) > 0
              or count_parts(p.get("inner")) > 0]
    print(f"{len(usable):,} plans have usable room geometry.")

    # Spread sample across the full dataset
    step   = max(1, len(usable) // args.limit)
    sample = usable[::step][: args.limit]
    print(f"Sampling {len(sample)} plans (every {step}th).")

    # ── 4. Render + index ────────────────────────────────────────────────────
    try:
        from tqdm import tqdm
        iterable = tqdm(sample, desc="Rendering")
    except ImportError:
        iterable = sample

    index: list[dict] = []
    rendered = 0
    skipped  = 0

    for plan in iterable:
        plan_id  = str(plan.get("id", f"plan-{len(index)}"))
        img_name = f"resplan-{plan_id}.png"
        img_path = out_dir / img_name
        img_url  = f"/floorplans/{img_name}"

        if not args.skip_render:
            try:
                render_plan_png(plan, img_path)
                rendered += 1
            except Exception as exc:
                print(f"  [WARN] Failed to render plan {plan_id}: {exc}")
                skipped += 1
                continue
        else:
            if not img_path.exists():
                skipped += 1
                continue

        try:
            entry = extract_entry(plan, img_url)
            index.append(entry)
        except Exception as exc:
            print(f"  [WARN] Failed to extract metadata for plan {plan_id}: {exc}")

    # ── 5. Write index ────────────────────────────────────────────────────────
    index_path = out_dir / "index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\n✓ Rendered {rendered} PNGs  ({skipped} skipped)")
    print(f"✓ Wrote {len(index)} entries → {index_path}")
    print(f"\nNext step:\n  cd apps/web && npm run dev\n  The app will now load real ResPlan floor plans.")


if __name__ == "__main__":
    main()
