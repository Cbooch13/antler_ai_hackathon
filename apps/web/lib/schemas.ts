import { z } from "zod";

export const sourceMetadataSchema = z.object({
  sourceName: z.string().min(1),
  sourceUrl: z.string().url(),
  retrievedAt: z.string().datetime(),
  confidence: z.enum(["low", "medium", "high"]),
  licenseName: z.string().nullable().optional(),
  notes: z.array(z.string()).default([])
});

export const userBuildSpecSchema = z.object({
  projectName: z.string().min(1),
  city: z.literal("Austin"),
  state: z.literal("TX"),
  propertyType: z.enum(["single_family", "adu", "duplex_triplex", "commercial"]),
  totalBudgetUsd: z.number().positive(),
  targetLotSqft: z.number().positive().optional(),
  targetBuildingSqft: z.number().positive().optional(),
  bedrooms: z.number().int().nonnegative().optional(),
  bathrooms: z.number().nonnegative().optional(),
  units: z.number().int().positive(),
  stylePreferences: z.array(z.string()).default([]),
  riskTolerance: z.enum(["low", "medium", "high"])
});

export const intakeNormalizeRequestSchema = z.object({
  freeText: z.string().default(""),
  structured: z.record(z.unknown()).default({})
});

export const normalizedBuildSpecResponseSchema = z.object({
  spec: userBuildSpecSchema.nullable(),
  missingFields: z.array(z.string()),
  assumptions: z.array(z.string()),
  warnings: z.array(z.string())
});

export const listingSchema = z.object({
  listingId: z.string().min(1),
  parcelId: z.string().nullable().optional(),
  address: z.string().min(1),
  neighborhood: z.string().nullable().optional(),
  priceUsd: z.number().positive(),
  lotSqft: z.number().positive().nullable().optional(),
  buildingSqft: z.number().positive().nullable().optional(),
  bedrooms: z.number().int().nonnegative().nullable().optional(),
  bathrooms: z.number().nonnegative().nullable().optional(),
  units: z.number().int().positive(),
  latitude: z.number().nullable().optional(),
  longitude: z.number().nullable().optional(),
  sourceMode: z.enum([
    "licensed",
    "prototype_static_dataset",
    "prototype_apify",
    "manual",
    "public"
  ]),
  currentInventory: z.boolean(),
  dataYear: z.number().int().nullable().optional(),
  prototypeNote: z.string().nullable().optional(),
  sources: z.array(sourceMetadataSchema)
});

export const parcelSchema = z.object({
  parcelId: z.string().min(1),
  address: z.string(),
  lotSqft: z.number().positive().nullable().optional(),
  zoning: z.string().nullable().optional(),
  latitude: z.number().nullable().optional(),
  longitude: z.number().nullable().optional(),
  sources: z.array(sourceMetadataSchema)
});

export const mapContextSchema = z.object({
  latitude: z.number().nullable().optional(),
  longitude: z.number().nullable().optional(),
  mapProvider: z.string(),
  aerialImageUrl: z.string().nullable().optional(),
  streetViewUrl: z.string().nullable().optional(),
  warnings: z.array(z.string())
});

export const rankedListingSchema = z.object({
  listing: listingSchema,
  score: z.number().min(0).max(100),
  rankReasons: z.array(z.string()),
  warnings: z.array(z.string())
});

export const lotSearchResponseSchema = z.object({
  sourceMode: z.enum([
    "licensed",
    "prototype_static_dataset",
    "prototype_apify",
    "manual",
    "public"
  ]),
  currentInventory: z.boolean(),
  candidates: z.array(rankedListingSchema),
  warnings: z.array(z.string()),
  source: sourceMetadataSchema.nullable().optional()
});

export const parcelDetailResponseSchema = z.object({
  listing: listingSchema,
  parcel: parcelSchema.nullable(),
  mapContext: mapContextSchema,
  zoningFeatures: z.array(z.unknown()),
  permitHistory: z.array(z.unknown()),
  warnings: z.array(z.string()),
  sources: z.array(sourceMetadataSchema)
});

export const complianceFindingSchema = z.object({
  code: z.string().min(1),
  title: z.string().min(1),
  status: z.enum(["passes", "fails", "warning", "unknown"]),
  summary: z.string().min(1),
  confidence: z.enum(["low", "medium", "high"]),
  professionalVerificationRequired: z.boolean(),
  citations: z.array(sourceMetadataSchema)
});

export const complianceMetricSchema = z.object({
  category: z.string().min(1),
  label: z.string().min(1),
  value: z.string().min(1),
  basis: z.enum(["known", "estimated", "public_data_pending", "unknown"]),
  status: z.enum(["passes", "fails", "warning", "unknown"]),
  confidence: z.enum(["low", "medium", "high"]),
  source: z.string().min(1),
  notes: z.string().nullable().optional()
});

export const complianceEvaluationResponseSchema = z.object({
  listing: listingSchema,
  parcel: parcelSchema,
  metrics: z.array(complianceMetricSchema),
  findings: z.array(complianceFindingSchema),
  summary: z.string().min(1),
  professionalVerificationRequired: z.boolean()
});

export const floorPlanRoomSchema = z.object({
  roomId: z.string().min(1),
  name: z.string().min(1),
  category: z.string().min(1),
  estimatedSqft: z.number().positive(),
  widthFt: z.number().positive(),
  depthFt: z.number().positive(),
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  width: z.number().positive().max(100),
  height: z.number().positive().max(100)
});

export const floorPlanWallSchema = z.object({
  wallId: z.string().min(1),
  x1: z.number().min(0).max(100),
  y1: z.number().min(0).max(100),
  x2: z.number().min(0).max(100),
  y2: z.number().min(0).max(100),
  wallType: z.string().min(1)
});

export const floorPlanOpeningSchema = z.object({
  openingId: z.string().min(1),
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  width: z.number().positive().max(100),
  orientation: z.enum(["horizontal", "vertical"]),
  openingType: z.string().min(1)
});

export const floorPlanConnectionSchema = z.object({
  connectionId: z.string().min(1),
  fromRoomId: z.string().min(1),
  toRoomId: z.string().min(1),
  connectionType: z.string().min(1),
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  width: z.number().positive().max(100),
  orientation: z.enum(["horizontal", "vertical"])
});

export const generatedVisualExportSchema = z.object({
  exportId: z.string().min(1),
  label: z.string().min(1),
  format: z.literal("svg"),
  content: z.string().min(1),
  notes: z.array(z.string())
});

export const floorPlanQualityCheckSchema = z.object({
  code: z.string().min(1),
  label: z.string().min(1),
  status: z.enum(["passes", "fails", "warning", "unknown"]),
  summary: z.string().min(1)
});

export const floorPlanQualityReportSchema = z.object({
  score: z.number().min(0).max(100),
  status: z.enum(["passes", "fails", "warning", "unknown"]),
  checks: z.array(floorPlanQualityCheckSchema),
  reviewNotes: z.array(z.string())
});

export const floorPlanSchema = z.object({
  planId: z.string().min(1),
  name: z.string().min(1),
  level: z.string().min(1),
  totalSqft: z.number().positive(),
  footprintWidthFt: z.number().positive(),
  footprintDepthFt: z.number().positive(),
  scaleAssumption: z.string().min(1),
  sqftDelta: z.number(),
  rooms: z.array(floorPlanRoomSchema),
  walls: z.array(floorPlanWallSchema),
  openings: z.array(floorPlanOpeningSchema),
  connections: z.array(floorPlanConnectionSchema),
  visualExports: z.array(generatedVisualExportSchema),
  qualityReport: floorPlanQualityReportSchema,
  notes: z.array(z.string())
});

export const designOptionSchema = z.object({
  optionId: z.string().min(1),
  name: z.string().min(1),
  strategy: z.string().min(1),
  targetBuildingSqft: z.number().positive(),
  units: z.number().int().positive(),
  floorPlans: z.array(floorPlanSchema),
  assumptions: z.array(z.string()),
  complianceFindings: z.array(complianceFindingSchema)
});

export const designGenerationResponseSchema = z.object({
  listing: listingSchema,
  parcel: parcelSchema,
  options: z.array(designOptionSchema),
  warnings: z.array(z.string())
});

export type UserBuildSpec = z.infer<typeof userBuildSpecSchema>;
export type IntakeNormalizeRequest = z.infer<typeof intakeNormalizeRequestSchema>;
export type NormalizedBuildSpecResponse = z.infer<typeof normalizedBuildSpecResponseSchema>;
export type LotSearchResponse = z.infer<typeof lotSearchResponseSchema>;
export type ParcelDetailResponse = z.infer<typeof parcelDetailResponseSchema>;
export type ComplianceFinding = z.infer<typeof complianceFindingSchema>;
export type ComplianceEvaluationResponse = z.infer<typeof complianceEvaluationResponseSchema>;
export type DesignGenerationResponse = z.infer<typeof designGenerationResponseSchema>;
