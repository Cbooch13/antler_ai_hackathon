import { describe, expect, it } from "vitest";
import {
  lotSearchResponseSchema,
  normalizedBuildSpecResponseSchema,
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
            address: "Central Austin prototype comp",
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
