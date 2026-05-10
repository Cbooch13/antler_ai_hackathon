import type { ValidatedContract } from '../types';
import { validatedContract } from '../data/mock';

export async function run(_freeText: string): Promise<ValidatedContract> {
  await new Promise<void>(r => setTimeout(r, 900));
  return validatedContract;
}
