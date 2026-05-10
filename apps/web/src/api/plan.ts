import type { Schematic } from '../types';
import { schematic } from '../data/mock';

export async function run(_lotId: string | null): Promise<Schematic> {
  await new Promise<void>(r => setTimeout(r, 2200));
  return schematic;
}
