"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  type ComplianceEvaluationResponse,
  type DesignGenerationResponse,
  type NormalizedBuildSpecResponse,
  type ParcelDetailResponse,
  type UserBuildSpec,
  complianceEvaluationResponseSchema,
  designGenerationResponseSchema,
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
  const [compliance, setCompliance] = useState<ComplianceEvaluationResponse | null>(null);
  const [designOptions, setDesignOptions] = useState<DesignGenerationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isNormalizing, setIsNormalizing] = useState(false);
  const [isSearchingLots, setIsSearchingLots] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isCheckingCompliance, setIsCheckingCompliance] = useState(false);
  const [isGeneratingDesign, setIsGeneratingDesign] = useState(false);

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
    setCompliance(null);
    setDesignOptions(null);
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
      setCompliance(null);
      setDesignOptions(null);
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
      setCompliance(null);
      setDesignOptions(null);
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
      setCompliance(null);
      setDesignOptions(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load parcel context.");
    } finally {
      setIsLoadingDetail(false);
    }
  }

  async function runFeasibilityCheck() {
    if (!result?.spec || !parcelDetail?.listing.listingId) {
      setError("Validate a spec and select a lot before running feasibility.");
      return;
    }

    setIsCheckingCompliance(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/compliance/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spec: result.spec,
          listingId: parcelDetail.listing.listingId
        })
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      setCompliance(complianceEvaluationResponseSchema.parse(await response.json()));
      setDesignOptions(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not run feasibility check.");
    } finally {
      setIsCheckingCompliance(false);
    }
  }

  async function generateSchematics() {
    if (!result?.spec || !parcelDetail?.listing.listingId) {
      setError("Validate a spec and select a lot before generating schematics.");
      return;
    }

    setIsGeneratingDesign(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/design/schematics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spec: result.spec,
          listingId: parcelDetail.listing.listingId
        })
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      setDesignOptions(designGenerationResponseSchema.parse(await response.json()));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not generate schematic options.");
    } finally {
      setIsGeneratingDesign(false);
    }
  }

  return (
    <section className="workspace" aria-label="Project intake">
      <div className="intake-grid">
        <form className="intake-form" onSubmit={handleSubmit(submitSpec)}>
          <div className="form-header">
            <p className="eyebrow">Stage 4</p>
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

        <aside className="preview">
          <h3>Validated Contract</h3>
          <pre>
            {JSON.stringify(result ?? (preview.success ? { spec: preview.data } : preview.error), null, 2)}
          </pre>
        </aside>
      </div>

      <section className="conversation-box">
        <label>
          Conversational request
          <textarea value={freeText} onChange={(event) => setFreeText(event.target.value)} />
        </label>
        <div className="action-row">
          <button type="button" onClick={normalizeText} disabled={isNormalizing}>
            {isNormalizing ? "Normalizing..." : "Normalize With API"}
          </button>
          <button type="button" onClick={searchPrototypeLots} disabled={isSearchingLots || !result?.spec}>
            {isSearchingLots ? "Searching..." : "Find Prototype Lots"}
          </button>
        </div>
        {error ? <div className="error">{error}</div> : null}
      </section>

      {lotSearch ? (
        <section className="results">
          <h3>Ranked Prototype Lots</h3>
          <div className="warning-list">
            {lotSearch.warnings.map((warning) => (
              <p className="warning" key={warning}>
                {warning}
              </p>
            ))}
          </div>
          <div className="result-list">
            {lotSearch.candidates.map((candidate) => (
              <article className="result-card" key={candidate.listing.listingId}>
                <div className="result-card-header">
                  <strong>Prototype Lot</strong>
                  <span>{candidate.score}/100</span>
                </div>
                <p className="address-line">{candidate.listing.address}</p>
                {candidate.listing.neighborhood ? (
                  <p className="area-line">{candidate.listing.neighborhood}</p>
                ) : null}
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
        </section>
      ) : null}

      {parcelDetail ? (
        <section className="parcel-detail">
          <h3>Lot Context</h3>
          <p className="section-address">{parcelDetail.listing.address}</p>
          {parcelDetail.listing.neighborhood ? (
            <p className="area-line">{parcelDetail.listing.neighborhood}</p>
          ) : null}
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
                  Open Map
                </a>
              ) : null}
          </div>
          <button type="button" onClick={runFeasibilityCheck} disabled={isCheckingCompliance}>
            {isCheckingCompliance ? "Checking..." : "Run Feasibility Check"}
          </button>
          {[...parcelDetail.warnings, ...parcelDetail.mapContext.warnings].map((warning) => (
            <p className="warning" key={warning}>
              {warning}
            </p>
          ))}
        </section>
      ) : null}

      {compliance ? (
        <section className="compliance-panel">
          <h3>Compliance Feasibility</h3>
          <p className="section-address">{compliance.listing.address}</p>
          <p>{compliance.summary}</p>
          <div className="compliance-table-wrap">
            <table className="compliance-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Value</th>
                  <th>Basis</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Source / Notes</th>
                </tr>
              </thead>
              <tbody>
                {compliance.metrics.map((metric) => (
                  <tr key={`${metric.category}-${metric.label}`}>
                    <td>
                      <strong>{metric.label}</strong>
                      <span>{metric.category}</span>
                    </td>
                    <td>{metric.value}</td>
                    <td>{metric.basis.replaceAll("_", " ")}</td>
                    <td>{metric.status}</td>
                    <td>{metric.confidence}</td>
                    <td>
                      {metric.source}
                      {metric.notes ? <span>{metric.notes}</span> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="finding-list">
            {compliance.findings.map((finding) => (
              <article className={`finding-card finding-${finding.status}`} key={finding.code}>
                <div className="result-card-header">
                  <strong>{finding.title}</strong>
                  <span>{finding.status}</span>
                </div>
                <p>{finding.summary}</p>
                <p>
                  Confidence: {finding.confidence} · Professional verification:{" "}
                  {finding.professionalVerificationRequired ? "required" : "not required"}
                </p>
              </article>
            ))}
          </div>
          <button type="button" onClick={generateSchematics} disabled={isGeneratingDesign}>
            {isGeneratingDesign ? "Generating..." : "Generate Schematic Options"}
          </button>
        </section>
      ) : null}

      {designOptions ? (
        <section className="design-panel">
          <h3>Schematic Options</h3>
          <p className="section-address">{designOptions.listing.address}</p>
          {designOptions.warnings.map((warning) => (
            <p className="warning" key={warning}>
              {warning}
            </p>
          ))}
          <div className="finding-list">
            {designOptions.options.map((option) => (
              <article className="finding-card" key={option.optionId}>
                <div className="result-card-header">
                  <strong>{option.name}</strong>
                  <span>{option.strategy.replaceAll("_", " ")}</span>
                </div>
                <p>
                  {option.targetBuildingSqft.toLocaleString()} sqft · {option.units} unit
                  {option.units === 1 ? "" : "s"}
                </p>
                {option.assumptions.map((assumption) => (
                  <p key={assumption}>{assumption}</p>
                ))}
                {option.floorPlans.map((plan) => (
                  <div className="floor-plan" key={plan.planId}>
                    <div className="result-card-header">
                      <strong>{plan.name}</strong>
                      <span>{plan.totalSqft.toLocaleString()} sqft</span>
                    </div>
                    <p>
                      Footprint: {plan.footprintWidthFt.toFixed(1)} ft x{" "}
                      {plan.footprintDepthFt.toFixed(1)} ft · {plan.scaleAssumption}
                    </p>
                    <div className={`quality-report quality-${plan.qualityReport.status}`}>
                      <div className="result-card-header">
                        <strong>Plan quality</strong>
                        <span>
                          {plan.qualityReport.status} · {Math.round(plan.qualityReport.score)}/100
                        </span>
                      </div>
                      <div className="quality-check-list">
                        {plan.qualityReport.checks.map((check) => (
                          <p className={`quality-check quality-${check.status}`} key={check.code}>
                            <strong>{check.label}:</strong> {check.summary}
                          </p>
                        ))}
                      </div>
                      {plan.qualityReport.reviewNotes.map((note) => (
                        <p key={note}>{note}</p>
                      ))}
                    </div>
                    {plan.visualExports[0] ? (
                      <div
                        className="floor-plan-export"
                        role="img"
                        aria-label={`${plan.name} conceptual architectural plan`}
                        dangerouslySetInnerHTML={{ __html: plan.visualExports[0].content }}
                      />
                    ) : null}
                    <div className="room-list">
                      {plan.rooms.map((room) => (
                        <span key={`${plan.planId}-${room.roomId}`}>
                          {room.name}: {room.estimatedSqft.toLocaleString()} sqft ·{" "}
                          {room.widthFt.toFixed(1)} ft x {room.depthFt.toFixed(1)} ft
                        </span>
                      ))}
                    </div>
                    <div className="context-links">
                      {plan.visualExports.map((visual) => (
                        <a
                          download={`${visual.exportId}.svg`}
                          href={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(visual.content)}`}
                          key={visual.exportId}
                        >
                          Download {visual.label}
                        </a>
                      ))}
                    </div>
                    {Math.abs(plan.sqftDelta) > 0.01 ? (
                      <p>Square-footage reconciliation delta: {plan.sqftDelta.toFixed(2)} sqft.</p>
                    ) : null}
                    {plan.notes.map((note) => (
                      <p key={note}>{note}</p>
                    ))}
                  </div>
                ))}
                <p>{option.complianceFindings.length} feasibility flags carried forward.</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}
