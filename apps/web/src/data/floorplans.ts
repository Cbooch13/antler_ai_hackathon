import type { FloorPlanEntry } from '../types';

// Fallback exemplar library used when ResPlan dataset images are not available.
// These match the 4 families used by the backend schematic agent in
// packages/agents/python/estate_agents/schematic.py (lines 166-298).
// License note applies to every entry.
const LICENSE_NOTE = 'Curated hackathon exemplar — not ResPlan or RPLAN. License review required before production use.';
const RESPLAN_NOTE = 'ResPlan academic dataset — license review required before production use.';

export const FALLBACK_PLANS: FloorPlanEntry[] = [
  {
    id: 'ex-central-hall-sm',
    name: 'Central Hall Bungalow — Small',
    family: 'central-hall',
    beds: 2, baths: 1, units: 1, sqftEstimate: 900, sqftRange: [700, 1100],
    propertyTypes: ['Single-family residence', 'ADU'],
    styleKeywords: ['craftsman', 'bungalow', 'traditional'],
    roomTypes: ['entry', 'living', 'kitchen', 'bedroom', 'bedroom', 'bathroom'],
    imageUrl: '/floorplans/ex-central-hall-sm.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
  {
    id: 'ex-central-hall-md',
    name: 'Central Hall Bungalow — Medium',
    family: 'central-hall',
    beds: 3, baths: 2, units: 1, sqftEstimate: 1600, sqftRange: [1300, 2000],
    propertyTypes: ['Single-family residence'],
    styleKeywords: ['craftsman', 'warm modern', 'traditional'],
    roomTypes: ['entry', 'living', 'dining', 'kitchen', 'bedroom', 'bedroom', 'bedroom', 'bathroom', 'bathroom'],
    imageUrl: '/floorplans/ex-central-hall-md.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
  {
    id: 'ex-central-hall-lg',
    name: 'Central Hall Bungalow — Large',
    family: 'central-hall',
    beds: 4, baths: 2, units: 1, sqftEstimate: 2200, sqftRange: [1900, 2600],
    propertyTypes: ['Single-family residence'],
    styleKeywords: ['craftsman', 'warm modern', 'natural light'],
    roomTypes: ['entry', 'living', 'dining', 'kitchen', 'bedroom', 'bedroom', 'bedroom', 'bedroom', 'bathroom', 'bathroom', 'laundry'],
    imageUrl: '/floorplans/ex-central-hall-lg.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
  {
    id: 'ex-side-hall-sm',
    name: 'Side Hall Infill Bar — Small',
    family: 'side-hall',
    beds: 2, baths: 1, units: 1, sqftEstimate: 1100, sqftRange: [900, 1400],
    propertyTypes: ['ADU', 'Single-family residence'],
    styleKeywords: ['modern', 'minimal', 'contemporary'],
    roomTypes: ['entry', 'living', 'kitchen', 'bedroom', 'bedroom', 'bathroom'],
    imageUrl: '/floorplans/ex-side-hall-sm.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
  {
    id: 'ex-side-hall-lg',
    name: 'Side Hall Infill Bar — Large',
    family: 'side-hall',
    beds: 3, baths: 2, units: 2, sqftEstimate: 2400, sqftRange: [1800, 3000],
    propertyTypes: ['Duplex', 'ADU'],
    styleKeywords: ['modern', 'warm modern', 'natural light'],
    roomTypes: ['entry', 'entry', 'living', 'living', 'kitchen', 'kitchen', 'bedroom', 'bedroom', 'bedroom', 'bathroom', 'bathroom'],
    imageUrl: '/floorplans/ex-side-hall-lg.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
  {
    id: 'ex-rear-adu-cottage',
    name: 'Rear ADU Cottage Pairing',
    family: 'rear-adu',
    beds: 4, baths: 3, units: 2, sqftEstimate: 2200, sqftRange: [1700, 2800],
    propertyTypes: ['ADU', 'Duplex'],
    styleKeywords: ['warm modern', 'natural light', 'craftsman'],
    roomTypes: ['entry', 'entry', 'living', 'dining', 'kitchen', 'bedroom', 'bedroom', 'bedroom', 'bedroom', 'bathroom', 'bathroom', 'bathroom', 'laundry'],
    imageUrl: '/floorplans/ex-rear-adu-cottage.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
  {
    id: 'ex-stacked-duplex-sm',
    name: 'Stacked Urban Duplex — Small',
    family: 'stacked-duplex',
    beds: 2, baths: 2, units: 2, sqftEstimate: 1800, sqftRange: [1400, 2200],
    propertyTypes: ['Duplex', 'Small multifamily'],
    styleKeywords: ['modern', 'contemporary', 'minimal'],
    roomTypes: ['entry', 'entry', 'living', 'living', 'kitchen', 'kitchen', 'bedroom', 'bedroom', 'bathroom', 'bathroom'],
    imageUrl: '/floorplans/ex-stacked-duplex-sm.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
  {
    id: 'ex-stacked-duplex-lg',
    name: 'Stacked Urban Duplex — Large',
    family: 'stacked-duplex',
    beds: 4, baths: 3, units: 2, sqftEstimate: 3200, sqftRange: [2400, 4200],
    propertyTypes: ['Duplex', 'Small multifamily', 'Townhome'],
    styleKeywords: ['modern', 'warm modern', 'contemporary'],
    roomTypes: ['entry', 'entry', 'living', 'living', 'dining', 'dining', 'kitchen', 'kitchen', 'bedroom', 'bedroom', 'bedroom', 'bedroom', 'bathroom', 'bathroom', 'bathroom'],
    imageUrl: '/floorplans/ex-stacked-duplex-lg.png',
    sourceDataset: 'fallback-exemplar',
    licenseNote: LICENSE_NOTE,
  },
];

// Attempt to load a pre-built ResPlan index from /floorplans/index.json.
// This file is generated by scripts/process_resplan.ts.
// Returns fallback plans if the index is not available.
let _resPlanIndex: FloorPlanEntry[] | null = null;

export async function loadFloorPlanIndex(): Promise<FloorPlanEntry[]> {
  if (_resPlanIndex !== null) return _resPlanIndex;
  try {
    const res = await fetch('/floorplans/index.json');
    if (!res.ok) throw new Error('index not found');
    const data = await res.json() as FloorPlanEntry[];
    _resPlanIndex = data.map(e => ({ ...e, licenseNote: RESPLAN_NOTE }));
    return _resPlanIndex;
  } catch {
    _resPlanIndex = FALLBACK_PLANS;
    return FALLBACK_PLANS;
  }
}

// Synchronous access to the cached index (or fallback if not yet loaded).
export function getFloorPlanIndex(): FloorPlanEntry[] {
  return _resPlanIndex ?? FALLBACK_PLANS;
}
