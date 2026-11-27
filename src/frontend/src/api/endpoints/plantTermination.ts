import { tenantClient as client } from '../client';
import type { TerminationOptions } from '../types';

/**
 * What the termination dialog offers for this plant: the cause-class pre-fill table resolved for it
 * (`GET /plant-instances/{key}/termination-options`, REQ-003 E5/E6, #2888).
 *
 * Its own module, not `plantInstances.ts`: that one is part of the initial bundle, and only the lazily loaded
 * plant detail page (through `TerminationDialog`) needs this read.
 */
export async function getTerminationOptions(key: string): Promise<TerminationOptions> {
  const { data } = await client.get<TerminationOptions>(`/plant-instances/${key}/termination-options`);
  return data;
}
