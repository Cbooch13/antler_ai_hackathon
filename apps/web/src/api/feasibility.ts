import type { ComplianceData } from '../types';
import { compliance } from '../data/mock';

export async function run(_lotId: string | null): Promise<ComplianceData> {
  await new Promise<void>(r => setTimeout(r, 1700));
  return compliance;
}
