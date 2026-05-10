import type { Intake, FloorPlanEntry } from '../types';

function styleOverlap(planKeywords: string[], intakePrefs: string[]): number {
  if (!planKeywords.length || !intakePrefs.length) return 0;
  const pref = intakePrefs.map(s => s.toLowerCase());
  return planKeywords.filter(k => pref.some(p => p.includes(k) || k.includes(p))).length;
}

function score(plan: FloorPlanEntry, intake: Intake): number {
  const sqftDelta = Math.abs(plan.sqftEstimate - intake.buildingSqft);
  const sqftPenalty = intake.buildingSqft > 0 ? (sqftDelta / intake.buildingSqft) * 60 : 0;
  const bedPenalty = Math.abs(plan.beds - intake.beds) * 10;
  const bathPenalty = Math.abs(plan.baths - intake.baths) * 10;
  const styleBonus = styleOverlap(plan.styleKeywords, intake.stylePreferences) * 5;
  return 100 - sqftPenalty - bedPenalty - bathPenalty + styleBonus;
}

function buildPool(intake: Intake, plans: FloorPlanEntry[]): FloorPlanEntry[] {
  const byType = plans.filter(p =>
    p.propertyTypes.includes(intake.propertyType) && p.units === intake.units
  );
  const byUnits = byType.length > 0 ? byType : plans.filter(p => p.units === intake.units);
  const pool = byUnits.length > 0 ? byUnits : plans;
  const byBeds = pool.filter(
    p => Math.abs(p.beds - intake.beds) <= 2 && Math.abs(p.baths - intake.baths) <= 2
  );
  return byBeds.length > 0 ? byBeds : pool;
}

export function rankPlans(intake: Intake, plans: FloorPlanEntry[], topN = 5): FloorPlanEntry[] {
  if (!plans.length) return [];
  const pool = buildPool(intake, plans);
  return [...pool].sort((a, b) => score(b, intake) - score(a, intake)).slice(0, topN);
}

export function selectPlan(intake: Intake, plans: FloorPlanEntry[]): FloorPlanEntry {
  const ranked = rankPlans(intake, plans, 1);
  if (!ranked.length) throw new Error('No floor plans available');
  return ranked[0];
}

export function fitScore(plan: FloorPlanEntry, intake: Intake): number {
  return Math.max(0, Math.min(100, Math.round(score(plan, intake))));
}
