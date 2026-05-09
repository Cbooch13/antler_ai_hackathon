"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  type NormalizedBuildSpecResponse,
  type ParcelDetailResponse,
  type UserBuildSpec,
  lotSearchResponseSchema,
  normalizedBuildSpecResponseSchema,
  parcelDetailResponseSchema,
  userBuildSpecSchema
} from "@/lib/schemas";
import type { LotSearchResponse } from "@/lib/schemas";

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
  const [lotSearch, setLotSearch] = useState<LotSearchResponse | null>(null);
  const [parcelDetail, setParcelDetail] = useState<ParcelDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isNormalizing, setIsNormalizing] = useState(false);
  const [isSearchingLots, setIsSearchingLots] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

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
    setLotSearch(null);
    setParcelDetail(null);
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
      setLotSearch(null);
      setParcelDetail(null);
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

  async function searchPrototypeLots() {
    if (!result?.spec) {
      setError("Validate or normalize a complete spec before searching lots.");
      return;
    }

    setIsSearchingLots(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/listings/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spec: result.spec,
          sourceMode: "prototype_static_dataset",
          limit: 5
        })
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(
            "Listings endpoint not found. Restart the FastAPI server so it is running Stage 3 or later."
          );
        }
        throw new Error(`API returned ${response.status}`);
      }

      setLotSearch(lotSearchResponseSchema.parse(await response.json()));
      setParcelDetail(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not search prototype lots.");
    } finally {
      setIsSearchingLots(false);
    }
  }

  async function loadParcelDetail(listingId: string) {
    setIsLoadingDetail(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/listings/${listingId}/detail`);

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      setParcelDetail(parcelDetailResponseSchema.parse(await response.json()));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load parcel context.");
    } finally {
      setIsLoadingDetail(false);
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
        <button type="button" onClick={searchPrototypeLots} disabled={isSearchingLots || !result?.spec}>
          {isSearchingLots ? "Searching..." : "Find Prototype Lots"}
        </button>

        {error ? <div className="error">{error}</div> : null}

        <div className="preview">
          <h3>Validated contract</h3>
          <pre>
            {JSON.stringify(result ?? (preview.success ? { spec: preview.data } : preview.error), null, 2)}
          </pre>
        </div>

        {lotSearch ? (
          <div className="results">
            <h3>Ranked Prototype Lots</h3>
            {lotSearch.warnings.map((warning) => (
              <p className="warning" key={warning}>
                {warning}
              </p>
            ))}
            <div className="result-list">
              {lotSearch.candidates.map((candidate) => (
                <article className="result-card" key={candidate.listing.listingId}>
                  <div>
                    <strong>{candidate.listing.address}</strong>
                    <span>{candidate.score}/100</span>
                  </div>
                  <p>
                    ${candidate.listing.priceUsd.toLocaleString()} ·{" "}
                    {candidate.listing.lotSqft?.toLocaleString() ?? "Unknown"} lot sqft ·{" "}
                    {candidate.listing.units} unit
                  </p>
                  <p>{candidate.listing.prototypeNote}</p>
                  <button
                    type="button"
                    onClick={() => loadParcelDetail(candidate.listing.listingId)}
                    disabled={isLoadingDetail}
                  >
                    {isLoadingDetail ? "Loading..." : "View Context"}
                  </button>
                </article>
              ))}
            </div>
          </div>
        ) : null}

        {parcelDetail ? (
          <div className="parcel-detail">
            <h3>Lot Context</h3>
            <strong>{parcelDetail.listing.address}</strong>
            <p>
              Coordinates: {parcelDetail.mapContext.latitude ?? "unknown"},{" "}
              {parcelDetail.mapContext.longitude ?? "unknown"}
            </p>
            {parcelDetail.mapContext.aerialImageUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={parcelDetail.mapContext.aerialImageUrl} alt="Aerial map context" />
            ) : null}
            <div className="context-links">
              {parcelDetail.mapContext.streetViewUrl ? (
                <a href={parcelDetail.mapContext.streetViewUrl} target="_blank" rel="noreferrer">
                  Open Street View
                </a>
              ) : null}
            </div>
            {[...parcelDetail.warnings, ...parcelDetail.mapContext.warnings].map((warning) => (
              <p className="warning" key={warning}>
                {warning}
              </p>
            ))}
          </div>
        ) : null}
      </aside>
    </section>
  );
}
