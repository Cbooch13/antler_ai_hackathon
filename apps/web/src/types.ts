// TypeScript types derived from wireframes/version2/data.js shapes

export interface Project {
  name: string;
  id: string;
  owner: string;
  updated: string;
}

export interface Intake {
  projectName: string;
  propertyType: string;
  riskTolerance: string;
  budget: number;
  units: number;
  lotSqft: number;
  buildingSqft: number;
  beds: number;
  baths: number;
  stylePreferences: string[];
}

export interface ValidatedContract {
  spec: {
    projectName: string;
    city: string;
    state: string;
    propertyType: string;
    totalBudgetUsd: number;
    targetLotSqft: number;
    targetBuildingSqft: number;
    bedrooms: number;
    bathrooms: number;
    units: number;
    stylePreferences: string[];
    riskTolerance: string;
  };
  missingFields: string[];
  assumptions: string[];
  warnings: string[];
}

export interface Lot {
  id: string;
  address: string;
  city: string;
  neighborhood: string;
  price: number;
  lotSqft: number;
  buildingSqft: number | null;
  beds: number;
  baths: number;
  units: number;
  score: number;
  coords: { lat: number; lng: number };
  reasons: string[];
}

export interface ComplianceRow {
  category: string;
  metric: string;
  value: string;
  basis: string;
  status: StatusKind;
  confidence: string;
  notes: string;
}

export interface ComplianceFindingItem {
  title: string;
  body: string;
}

export interface ComplianceFindingsGrouped {
  passes: ComplianceFindingItem[];
  warnings: ComplianceFindingItem[];
  unknowns: ComplianceFindingItem[];
  fails: ComplianceFindingItem[];
}

export interface ComplianceData {
  findings: number;
  needsReview: number;
  rows: ComplianceRow[];
  findingsGrouped: ComplianceFindingsGrouped;
}

export interface Room {
  name: string;
  category: string;
  sqft: number;
  dim: string;
  level: number;
}

export interface QualityCheck {
  name: string;
  status: 'pass' | 'fail';
  body: string;
}

export interface Schematic {
  name: string;
  targetSqft: number;
  units: number;
  qualityScore: number;
  qualityStatus: string;
  massing: string;
  revisionNotes: string[];
  rooms: Room[];
  qualityChecks: QualityCheck[];
}

export interface PacketDocument {
  name: string;
  required: boolean;
  status: string;
  file: string | null;
}

export interface PacketGroup {
  role: string;
  status: string;
  notes: string;
  documents: PacketDocument[];
}

export interface PacketData {
  groups: PacketGroup[];
}

// Workflow types

export type Screen =
  | 'intake'
  | 'lots'
  | 'lot-context'
  | 'compliance'
  | 'schematic'
  | 'packet';

export type JobName = 'validate' | 'normalize' | 'findLots' | 'feasibility' | 'plan';

export type RunStatus = 'idle' | 'loading' | 'done' | 'error';

export type RunStates = Partial<Record<JobName, RunStatus>>;

export interface WorkflowState {
  screen: Screen;
  step: number;
  validated: boolean;
  selectedLotId: string | null;
  intake: Intake;
  conversation: string;
}

export type StatusKind = 'passes' | 'warning' | 'fail' | 'unknown' | 'info';
