import type { BedStatus } from '../model/types';

/**
 * The transitions of the bed lifecycle (V-10, GP-API-018): planned to active or retired, active to
 * retired, retired back to active. Retiring and reactivating are the lead's; a grower may only
 * bring a planned bed into use. Mirrors the server so the dialog offers nothing that is refused.
 */
export function allowedBedTransitions(current: BedStatus, isLead: boolean): BedStatus[] {
  if (current === 'planned') return isLead ? ['active', 'retired'] : ['active'];
  if (current === 'active') return isLead ? ['retired'] : [];
  return isLead ? ['active'] : [];
}
