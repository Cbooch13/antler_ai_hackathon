import type { Intake, Lot } from '../types';
import { lots } from '../data/mock';

export async function run(_intake: Intake): Promise<Lot[]> {
  await new Promise<void>(r => setTimeout(r, 1500));
  return lots;
}
