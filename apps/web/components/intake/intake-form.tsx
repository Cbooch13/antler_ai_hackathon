"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  type NormalizedBuildSpecResponse,
  type UserBuildSpec,
  normalizedBuildSpecResponseSchema,
  userBuildSpecSchema
} from "@/lib/schemas";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const defaultValues: UserBuildSpec = {
  projectName: "Austin ADU feasibility",
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
};

export function IntakeForm() {
  const [freeText, setFreeText] = useState(
    "I want an ADU-friendly warm modern home in Austin with 4 beds, 3 baths, 2 units, 2200 sqft house, 6500 lot sqft, and a budget of 850k."
  );
  const [result, setResult] = useState<NormalizedBuildSpecResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isNormalizing, setIsNormalizing] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch
  } = useForm<UserBuildSpec>({
    resolver: zodResolver(userBuildSpecSchema),
    defaultValues
  });

  const currentSpec = watch();
  const preview = useMemo(() => userBuildSpecSchema.safeParse(currentSpec), [currentSpec]);

  async function submitSpec(values: UserBuildSpec) {
    setError(null);
    setResult({
      spec: values,
      missingFields: [],
      assumptions: ["Structured intake fields validated locally."],
      warnings:
        values.propertyType === "commercial"
          ? ["Commercial intake is captured, but MVP feasibility confidence is limited."]
          : []
    });
  }

  async function normalizeText() {
    setIsNormalizing(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/intake/normalize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ freeText, structured: {} })
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const parsed = normalizedBuildSpecResponseSchema.parse(await response.json());
      setResult(parsed);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not normalize intake text. Is the FastAPI server running?"
      );
    } finally {
      setIsNormalizing(false);
    }
  }

  return (
    <section className="intake-grid" aria-label="Project intake">
      <form className="intake-form" onSubmit={handleSubmit(submitSpec)}>
        <div className="form-header">
          <p className="eyebrow">Stage 1</p>
          <h2>Project Intake</h2>
        </div>

        <label>
          Project name
          <input {...register("projectName")} />
          {errors.projectName ? <span>{errors.projectName.message}</span> : null}
        </label>

        <div className="field-row">
          <label>
            Property type
            <select {...register("propertyType")}>
              <option value="single_family">Single family</option>
              <option value="adu">ADU</option>
              <option value="duplex_triplex">Duplex/triplex</option>
              <option value="commercial">Commercial</option>
            </select>
          </label>

          <label>
            Risk
            <select {...register("riskTolerance")}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
        </div>

        <div className="field-row">
          <label>
            Budget
            <input type="number" {...register("totalBudgetUsd", { valueAsNumber: true })} />
          </label>

          <label>
            Units
            <input type="number" {...register("units", { valueAsNumber: true })} />
          </label>
        </div>

        <div className="field-row">
          <label>
            Lot sqft
            <input type="number" {...register("targetLotSqft", { valueAsNumber: true })} />
          </label>

          <label>
            Building sqft
            <input type="number" {...register("targetBuildingSqft", { valueAsNumber: true })} />
          </label>
        </div>

        <div className="field-row">
          <label>
            Beds
            <input type="number" {...register("bedrooms", { valueAsNumber: true })} />
          </label>

          <label>
            Baths
            <input type="number" step="0.5" {...register("bathrooms", { valueAsNumber: true })} />
          </label>
        </div>

        <input type="hidden" value="Austin" {...register("city")} />
        <input type="hidden" value="TX" {...register("state")} />

        <button type="submit">Validate Spec</button>
      </form>

      <aside className="intake-side">
        <label>
          Conversational request
          <textarea value={freeText} onChange={(event) => setFreeText(event.target.value)} />
        </label>
        <button type="button" onClick={normalizeText} disabled={isNormalizing}>
          {isNormalizing ? "Normalizing..." : "Normalize With API"}
        </button>

        {error ? <div className="error">{error}</div> : null}

        <div className="preview">
          <h3>Validated contract</h3>
          <pre>
            {JSON.stringify(result ?? (preview.success ? { spec: preview.data } : preview.error), null, 2)}
          </pre>
        </div>
      </aside>
    </section>
  );
}
