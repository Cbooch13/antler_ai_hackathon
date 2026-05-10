import type { LotGeometry } from '../types';

const TCAD_BASE =
  'https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/EXTERNAL_tcad_parcel/FeatureServer/0/query';

interface ArcGisResponse {
  features?: Array<{
    attributes: Record<string, unknown>;
    geometry?: {
      rings?: [number, number][][];
    };
  }>;
}

function centroidFromRings(rings: [number, number][][]): { lat: number; lng: number } {
  const outer = rings[0] ?? [];
  if (!outer.length) return { lat: 0, lng: 0 };
  const sumLng = outer.reduce((s, p) => s + p[0], 0) / outer.length;
  const sumLat = outer.reduce((s, p) => s + p[1], 0) / outer.length;
  return { lat: sumLat, lng: sumLng };
}

function ringsToSqft(rings: [number, number][][]): number {
  // Shoelace formula in degrees → convert to sqft (rough: 1 degree lat ≈ 364,000 ft at Austin lat)
  const outer = rings[0] ?? [];
  if (outer.length < 3) return 0;
  let area = 0;
  for (let i = 0; i < outer.length; i++) {
    const j = (i + 1) % outer.length;
    area += outer[i][0] * outer[j][1];
    area -= outer[j][0] * outer[i][1];
  }
  const degSq = Math.abs(area) / 2;
  // At Austin (~30°N): 1° lng ≈ 315,800 ft, 1° lat ≈ 364,000 ft
  return Math.round(degSq * 315800 * 364000);
}

export async function fetchLotGeometry(
  address: string,
  city: string
): Promise<LotGeometry | null> {
  const streetPart = address.split(',')[0].trim().toUpperCase();
  const where = `UPPER(SITUS_ADDR) LIKE '${streetPart}%'`;
  const params = new URLSearchParams({
    where,
    outFields: 'PROP_ID,SITUS_ADDR,LAND_SQFT',
    returnGeometry: 'true',
    geometryPrecision: '6',
    outSR: '4326',
    resultRecordCount: '5',
    f: 'json',
  });

  try {
    const res = await fetch(`${TCAD_BASE}?${params.toString()}`);
    if (!res.ok) return null;
    const data: ArcGisResponse = await res.json();
    const feature = data.features?.[0];
    if (!feature) return null;

    const rings = feature.geometry?.rings ?? [];
    const attrs = feature.attributes;
    const parcelId = attrs['PROP_ID'] ? String(attrs['PROP_ID']) : null;
    const landSqft = typeof attrs['LAND_SQFT'] === 'number'
      ? (attrs['LAND_SQFT'] as number)
      : ringsToSqft(rings);

    return {
      rings,
      centroid: centroidFromRings(rings),
      lotSqft: Math.round(landSqft),
      parcelId,
    };
  } catch {
    return null;
  }
}
