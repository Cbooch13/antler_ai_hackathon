import type { Intake, ValidatedContract } from '../types';
import { validatedContract } from '../data/mock';

export async function run(_intake: Intake): Promise<ValidatedContract> {
  await new Promise<void>(r => setTimeout(r, 700));
  return validatedContract;
}
