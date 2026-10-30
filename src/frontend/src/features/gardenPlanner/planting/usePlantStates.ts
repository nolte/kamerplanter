import { useCallback, useEffect, useMemo, useState } from 'react';
import { computePlantState, type PhaseFacts, type PlantVisualState } from '../model/plantState';
import { listPlantStates, type PlantStateWire } from './plantStateApi';
import { stateInstant, usePlantStateClock } from './plantStateClock';

/** A plant of the answer with the state the port computed at the current instant (GP-FR-192). */
export interface PlantStateView extends PlantStateWire {
  visual: PlantVisualState;
}

export function visualOf(wire: PlantStateWire, now: string): PlantVisualState {
  const phase: PhaseFacts | null = wire.inputs.phase
    ? {
        key: wire.inputs.phase.key,
        started_on: wire.inputs.phase.started_on,
        typical_days: wire.inputs.phase.typical_days ?? null,
        allows_harvest: wire.inputs.phase.allows_harvest,
        is_terminal: wire.inputs.phase.is_terminal,
      }
    : null;
  return computePlantState(
    { kind: 'plant', removed_on: null, termination_type: null },
    phase,
    wire.inputs.open_tasks.map((task) => ({ category: task.category, due: task.due ?? null })),
    {
      open_findings: wire.inputs.open_findings,
      frost_risk: wire.inputs.frost_risk,
      harvest_batches: wire.inputs.harvest_batches,
      now,
    },
  );
}

/** The answer of one bed as views by plant key, computed for the instant `now`. */
export function viewsOf(items: readonly PlantStateWire[], now: string): Record<string, PlantStateView> {
  return Object.fromEntries(
    items.map((wire): [string, PlantStateView] => [wire.plant_key, { ...wire, visual: visualOf(wire, now) }]),
  );
}

export interface UsePlantStates {
  /** By plant key; empty until the first answer, and after a failure (the plan stays usable without states). */
  states: Readonly<Record<string, PlantStateView>>;
  /** When the answer arrived (epoch ms); `null` before it. */
  loadedAt: number | null;
  /** Load again, e.g. after a plan or care action (GP-FR-191). */
  refresh: () => void;
}

/**
 * The plant states of one bed: loaded once per bed, again on `refresh()` and when the page comes back to the
 * foreground (GP-FR-191); the visual state is recomputed every minute so a task that turns overdue at midnight
 * shows without a request. Hovering reads this state and never requests anything.
 */
export function usePlantStates(bedKey: string | null, enabled = true): UsePlantStates {
  const [wires, setWires] = useState<{ bedKey: string; items: PlantStateWire[]; loadedAt: number } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const refresh = useCallback(() => setAttempt((value) => value + 1), []);
  const day = usePlantStateClock(enabled, refresh);

  useEffect(() => {
    if (!enabled || !bedKey) return undefined;
    const abort = new AbortController();
    listPlantStates(bedKey, abort.signal)
      .then((items) => {
        if (!abort.signal.aborted) setWires({ bedKey, items, loadedAt: Date.now() });
      })
      .catch(() => {
        // States are an enhancement of the plan: a failed read leaves the plain markers.
      });
    return () => abort.abort();
  }, [bedKey, enabled, attempt]);

  const current = wires && wires.bedKey === bedKey ? wires : null;
  const states = useMemo(() => {
    if (!current) return {};
    // `day` is the clock: the state is recomputed when the answer or the day changes, not every minute.
    const now = stateInstant(day);
    return viewsOf(current.items, now);
  }, [current, day]);
  const loadedAt = current?.loadedAt ?? null;
  return useMemo(() => ({ states, loadedAt, refresh }), [states, loadedAt, refresh]);
}
