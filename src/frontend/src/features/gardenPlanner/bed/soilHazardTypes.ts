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

/**
 * Which soil hazards a location takes (`soil_hazard_scope` of the location summary, AP-API-012, REQ-053 §11.3a Nr. 5
 * v1.60): `all` a bed, `juglone_only` an area that is no bed (garden, zone, greenhouse on grown soil), `container` a
 * vessel, `hydroponic` a location whose own or inherited irrigation system has no soil. The server decides it - also
 * the irrigation system a shelf inherits from a hydroponic room - so the page never recomputes the rule.
 */
export type SoilHazardScope = 'all' | 'juglone_only' | 'container' | 'hydroponic';

/** Why a location takes no soil hazard at all - what the server would refuse it with - or `null` when it takes one. */
export function soilHazardsUnavailable(scope: SoilHazardScope): 'container' | 'hydroponic' | null {
  return scope === 'container' || scope === 'hydroponic' ? scope : null;
}

/** The hazards the form offers at a location of this scope (an area takes juglone only). */
export function recordableSoilHazards(scope: SoilHazardScope): readonly SoilHazard[] {
  if (scope === 'all') return SOIL_HAZARDS;
  if (scope === 'juglone_only') return ['juglone'];
  return [];
}
