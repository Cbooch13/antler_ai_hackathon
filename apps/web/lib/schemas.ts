import { z } from "zod";

export const sourceMetadataSchema = z.object({
  sourceName: z.string().min(1),
  sourceUrl: z.string().url(),
  retrievedAt: z.string().datetime(),
  confidence: z.enum(["low", "medium", "high"])
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
export type ComplianceFinding = z.infer<typeof complianceFindingSchema>;
