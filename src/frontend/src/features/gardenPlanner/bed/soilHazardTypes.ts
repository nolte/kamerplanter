/**
 * The soil hazards of a bed (REQ-054 §5.2, AP-API-012, #2888 F-20) as the server answers them. The entry stores the
 * hazard key, the confirmation date and how it was confirmed (a category, never a person); pathogens and hosts come
 * from the knowledge table at read time, each host with its evidence status as data.
 */
import type { PathogenConfirmationSource, SoilHazard } from '@/api/types';

/** Mirrors `HostLevel` of `app/common/enums.py`. */
export type SoilHazardHostLevel = 'family' | 'genus' | 'species';
/** Mirrors `EvidenceStatus` of `app/common/enums.py`; only `evidenced` is backed by three sources (3/3). */
export type SoilHazardEvidenceStatus = 'evidenced' | 'insufficient' | 'contradictory' | 'not_found';

export interface SoilHazardHost {
  level: SoilHazardHostLevel;
  /** APG IV family name, genus or scientific species name. */
  name: string;
  evidence_status: SoilHazardEvidenceStatus;
}

export interface BedSoilHazard {
  hazard: SoilHazard;
  /** ISO date; for `juglone` the felling of the walnut tree. */
  confirmed_at: string;
  source: PathogenConfirmationSource;
  pathogens: string[];
  /** Host range so broad that the hazard never warns, only hints (REQ-054 §5.2a). */
  soft: boolean;
  hosts: SoilHazardHost[];
  non_hosts: SoilHazardHost[];
}

/** `POST /locations/{key}/soil-hazards`: the bed's hazards after the write. */
export interface LocationSoilHazards {
  location_key: string;
  /** `false` (status 200): nothing written - the bed already carries the hazard confirmed as late or later. */
  changed: boolean;
  soil_hazards: BedSoilHazard[];
}

/** A hazard entered by hand. */
export interface SoilHazardBody {
  hazard: SoilHazard;
  confirmed_at: string;
  source: PathogenConfirmationSource;
}

/**
 * What the app proposes after a soil-borne loss (REQ-053 §11.3a Nr. 5): `offer` - take the confirmed pathogen over
 * into the bed (nothing is written until the user confirms); `clean_system` - a hydroponic location, no soil hazard.
 */
export interface SoilHazardFollowUp {
  kind: 'offer' | 'clean_system';
  location_key: string;
  hazard?: SoilHazard | null;
  confirmed_at?: string | null;
  source?: PathogenConfirmationSource | null;
}

/** The hazards in the server's order (`SoilHazard` of `app/common/enums.py`). */
export const SOIL_HAZARDS: readonly SoilHazard[] = [
  'clubroot',
  'cyst_nematode',
  'root_knot_nematode',
  'white_rot',
  'pea_root_rot',
  'sclerotinia',
  'verticillium',
  'juglone',
];

/** How a hazard was confirmed (`PathogenConfirmationSource`): a category, never a person. */
export const CONFIRMATION_SOURCES: readonly PathogenConfirmationSource[] = [
  'lab_test',
  'advisory_service',
  'clear_symptoms',
];

/** Vessels carry no soil hazard: their substrate is replaced (REQ-053 §11.3a Nr. 5; the server refuses them). */
export const CONTAINER_LOCATION_TYPES: ReadonlySet<string> = new Set(['planter', 'tent', 'shelf']);
/** No bed type but a vessel all the same (pot/container group): the server answers it with the vessel refusal. */
export const NON_BED_VESSEL_LOCATION_TYPES: ReadonlySet<string> = new Set(['container']);
/** Irrigation systems without soil (`Location.irrigation_system` is authoritative). */
export const HYDROPONIC_IRRIGATION_SYSTEMS: ReadonlySet<string> = new Set(['hydro', 'nft', 'ebb_flow']);

/** Why a location carries no soil hazard - what the server would refuse it with - or `null` when it may. */
export function soilHazardsUnavailable(
  locationTypeKey: string,
  irrigationSystem: string | null | undefined,
): 'container' | 'hydroponic' | null {
  if (CONTAINER_LOCATION_TYPES.has(locationTypeKey) || NON_BED_VESSEL_LOCATION_TYPES.has(locationTypeKey)) {
    return 'container';
  }
  if (irrigationSystem && HYDROPONIC_IRRIGATION_SYSTEMS.has(irrigationSystem)) return 'hydroponic';
  return null;
}
