import { useMemo } from 'react';
import { useNutrientPlanData } from './useNutrientPlanData';
import { useNutrientPlanActions } from './useNutrientPlanActions';

/**
 * Composed controller for the nutrient-plan detail page (AP-20). Wires the
 * read/entity side ({@link useNutrientPlanData}) to the write/timeline side
 * ({@link useNutrientPlanActions}) — the latter refreshes the page through the
 * former's `load`. Both parts return memo-stable objects, so the merged result
 * only changes when one of them does. The orchestrator consumes this single hook.
 */
export function useNutrientPlanDetail() {
  const data = useNutrientPlanData();
  const actions = useNutrientPlanActions({
    key: data.key,
    plan: data.plan,
    entries: data.entries,
    fertilizers: data.fertilizers,
    load: data.load,
  });
  return useMemo(() => ({ ...data, ...actions }), [data, actions]);
}
