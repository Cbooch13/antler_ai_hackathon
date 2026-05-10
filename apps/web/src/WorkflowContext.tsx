import { createContext, useContext } from 'react';
import type { WorkflowState, JobName, RunStates, Screen } from './types';

export interface WorkflowContextValue {
  state: WorkflowState;
  setState: React.Dispatch<React.SetStateAction<WorkflowState>>;
  run: (job: JobName) => void;
  runStates: RunStates;
  goTo: (key: Screen) => void;
  advanceTo: (key: Screen, minStep: number) => void;
}

export const WorkflowContext = createContext<WorkflowContextValue | null>(null);

export function useWorkflow(): WorkflowContextValue {
  const ctx = useContext(WorkflowContext);
  if (!ctx) throw new Error('useWorkflow must be used inside WorkspaceShell');
  return ctx;
}
