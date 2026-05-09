import { describe, expect, it } from "vitest";
import {
  lotSearchResponseSchema,
  complianceEvaluationResponseSchema,
  normalizedBuildSpecResponseSchema,
  parcelDetailResponseSchema,
  userBuildSpecSchema
} from "../lib/schemas";

describe("userBuildSpecSchema", () => {
  it("accepts a valid Austin residential infill spec", () => {
    const result = userBuildSpecSchema.safeParse({
      projectName: "Mueller ADU feasibility",
      city: "Austin",
      state: "TX",
      propertyType: "adu",
      totalBudgetUsd: 850000,
      targetLotSqft: 6500,
      targetBuildingSqft: 2200,
      bedrooms: 4,
      bathrooms: 3,
      units: 2,
      stylePreferences: ["warm modern", "natural light"],
      riskTolerance: "medium"
    });

    expect(result.success).toBe(true);
  });

  it("rejects invalid budgets", () => {
    const result = userBuildSpecSchema.safeParse({
      projectName: "Bad budget",
      city: "Austin",
      state: "TX",
      propertyType: "single_family",
      totalBudgetUsd: 0,
      units: 1,
      riskTolerance: "low"
    });

    expect(result.success).toBe(false);
  });
});

describe("normalizedBuildSpecResponseSchema", () => {
  it("accepts missing field prompts without a spec", () => {
    const result = normalizedBuildSpecResponseSchema.safeParse({
      spec: null,
      missingFields: ["totalBudgetUsd"],
      assumptions: ["Assumed single-family residential."],
      warnings: []
    });

    expect(result.success).toBe(true);
  });
});

describe("lotSearchResponseSchema", () => {
  it("requires prototype listings to expose inventory status", () => {
    const result = lotSearchResponseSchema.safeParse({
      sourceMode: "prototype_static_dataset",
      currentInventory: false,
      warnings: ["Static dataset only."],
      source: null,
      candidates: [
        {
          score: 91,
          rankReasons: ["At or below budget."],
          warnings: ["Static comp only, not active inventory."],
          listing: {
            listingId: "kaggle-austin-001",
            address: "4307 Avenue G, Austin, TX 78751",
            neighborhood: "Hyde Park / Central Austin",
            priceUsd: 825000,
            lotSqft: 6600,
            units: 2,
            sourceMode: "prototype_static_dataset",
            currentInventory: false,
            dataYear: 2021,
            sources: []
          }
        }
      ]
    });

    expect(result.success).toBe(true);
  });
});

describe("parcelDetailResponseSchema", () => {
  it("accepts lot context with missing-data warnings", () => {
    const result = parcelDetailResponseSchema.safeParse({
      listing: {
        listingId: "kaggle-austin-001",
        address: "4307 Avenue G, Austin, TX 78751",
        neighborhood: "Hyde Park / Central Austin",
        priceUsd: 825000,
        lotSqft: 6600,
        units: 2,
        sourceMode: "prototype_static_dataset",
        currentInventory: false,
        sources: []
      },
      parcel: null,
      mapContext: {
        latitude: 30.298,
        longitude: -97.741,
        mapProvider: "mapbox",
        aerialImageUrl: null,
        streetViewUrl:
          "https://www.google.com/maps/search/?api=1&query=4307+Avenue+G%2C+Austin%2C+TX+78751",
        warnings: ["Mapbox token is not configured."]
      },
      zoningFeatures: [],
      permitHistory: [],
      warnings: ["No zoning feature has been joined yet."],
      sources: []
    });

    expect(result.success).toBe(true);
  });
});

describe("complianceEvaluationResponseSchema", () => {
  it("accepts advisory feasibility findings", () => {
    const result = complianceEvaluationResponseSchema.safeParse({
      listing: {
        listingId: "kaggle-austin-001",
        address: "4307 Avenue G, Austin, TX 78751",
        neighborhood: "Hyde Park / Central Austin",
        priceUsd: 825000,
        units: 2,
        sourceMode: "prototype_static_dataset",
        currentInventory: false,
        sources: []
      },
      parcel: {
        parcelId: "prototype-kaggle-austin-001",
        address: "4307 Avenue G, Austin, TX 78751",
        sources: []
      },
      findings: [
        {
          code: "STATIC-DATASET-SOURCE",
          title: "Static fallback data",
          status: "warning",
          summary: "This property comes from a static MVP fallback dataset.",
          confidence: "high",
          professionalVerificationRequired: true,
          citations: []
        }
      ],
      metrics: [
        {
          category: "Setbacks",
          label: "Front setback",
          value: "25 ft estimate",
          basis: "estimated",
          status: "warning",
          confidence: "low",
          source: "Austin Land Development Code",
          notes: "Advisory estimate."
        }
      ],
      summary: "1 advisory finding generated; 1 requires review or additional data.",
      professionalVerificationRequired: true
    });

    expect(result.success).toBe(true);
  });
});
