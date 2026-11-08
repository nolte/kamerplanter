import { useMemo } from 'react';
import type { PlanModel } from '../model/planModel';
import type { PlantMarkerState } from '../renderer/types';
import { colorsOf, usePhaseNames } from './phaseColors';
import type { UsePlanPlantStates } from './usePlanPlantStates';

const NO_PHASE_KEYS: readonly (string | null | undefined)[] = [];

export interface PlantStateLayerOptions {
  /** Phase keys of the plants whose states are loaded (for the legend); empty while the layer is off. */
  planPhaseKeys: readonly (string | null | undefined)[];
  /** `phase key → name`: from the state answers, completed by `/growth-phases/{key}` (the fetched name wins). */
  phaseNames: Readonly<Record<string, string>>;
  /** `phase key → colour` for the marker fill (GP-FR-067). */
  phaseColors: Readonly<Record<string, string>>;
  /** The renderer's `plantStateLayer`; `undefined` while the layer is off. */
  plantStateLayer: { states: Readonly<Record<string, PlantMarkerState>>; attentionOnly: boolean } | undefined;
}

/**
 * The render options of the plant-state layer (REQ-053 GP-UX-061, GP-FR-067), shared by the editor and the PNG
 * export so both draw the same markers: phase names are read only for the plants whose states are loaded (beds at
 * marker LOD), never for the whole plan.
 */
export function usePlantStateLayer(
  plan: PlanModel | null,
  planStates: Pick<UsePlanPlantStates, 'states' | 'phaseNames'>,
  enabled: boolean,
  attentionOnly: boolean,
): PlantStateLayerOptions {
  const plants = plan?.plants;
  const planPhaseKeys = useMemo(() => {
    const plantKeys = Object.keys(planStates.states);
    return enabled && plants && plantKeys.length > 0
      ? plantKeys.map((plantKey) => plants[plantKey]?.phase_key)
      : NO_PHASE_KEYS;
  }, [enabled, planStates.states, plants]);
  const fetchedPhaseNames = usePhaseNames(planPhaseKeys);
  // A phase-sequence entry key is unknown to `/growth-phases/{key}`; the state answer names it. The fetched name wins.
  const phaseNames = useMemo(
    () => ({ ...planStates.phaseNames, ...fetchedPhaseNames }),
    [planStates.phaseNames, fetchedPhaseNames],
  );
  const phaseColors = useMemo(() => colorsOf(phaseNames), [phaseNames]);
  const plantStateLayer = useMemo(
    () => (enabled ? { states: planStates.states, attentionOnly } : undefined),
    [enabled, planStates.states, attentionOnly],
  );
  return useMemo(
    () => ({ planPhaseKeys, phaseNames, phaseColors, plantStateLayer }),
    [planPhaseKeys, phaseNames, phaseColors, plantStateLayer],
  );
}
