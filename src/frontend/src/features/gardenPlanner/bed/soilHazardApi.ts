import { tenantClient } from '@/api/client';
import type { SoilHazard } from '@/api/types';
import type { LocationSoilHazards, SoilHazardBody } from './soilHazardTypes';

/**
 * AP-API-012 (REQ-054 §5.2, #2888 F-20): the soil hazards of a bed. They are read with the location
 * (`soil_hazards[]` on the bed summary); here are the two writes. Recording is open to growers, removing to the
 * lead - the server is the gate, the UI only hides what the role cannot do.
 */

const LOCATIONS = '/locations';

/** Record a confirmed soil hazard by hand; a later confirmation of the same hazard replaces the stored one. */
export async function recordSoilHazard(bedKey: string, body: SoilHazardBody): Promise<LocationSoilHazards> {
  const { data } = await tenantClient.post<LocationSoilHazards>(`${LOCATIONS}/${bedKey}/soil-hazards`, body);
  return data;
}

/**
 * Accept the offer after a loss: the server takes the confirmed pathogen, the day and the source from the stored
 * loss of `plantKey` - the client sends nothing else, so an unconfirmed loss cannot become an entry.
 */
export async function takeOverLossAsSoilHazard(bedKey: string, plantKey: string): Promise<LocationSoilHazards> {
  const { data } = await tenantClient.post<LocationSoilHazards>(`${LOCATIONS}/${bedKey}/soil-hazards`, {
    plant_key: plantKey,
  });
  return data;
}

/** Remove a soil hazard from the bed (lead only). */
export async function removeSoilHazard(bedKey: string, hazard: SoilHazard): Promise<void> {
  await tenantClient.delete(`${LOCATIONS}/${bedKey}/soil-hazards/${hazard}`);
}
