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

export const complianceFindingSchema = z.object({
  code: z.string().min(1),
  title: z.string().min(1),
  status: z.enum(["passes", "fails", "warning", "unknown"]),
  summary: z.string().min(1),
  confidence: z.enum(["low", "medium", "high"]),
  professionalVerificationRequired: z.boolean(),
  citations: z.array(sourceMetadataSchema)
});

export type UserBuildSpec = z.infer<typeof userBuildSpecSchema>;
export type IntakeNormalizeRequest = z.infer<typeof intakeNormalizeRequestSchema>;
export type NormalizedBuildSpecResponse = z.infer<typeof normalizedBuildSpecResponseSchema>;
export type LotSearchResponse = z.infer<typeof lotSearchResponseSchema>;
export type ComplianceFinding = z.infer<typeof complianceFindingSchema>;
