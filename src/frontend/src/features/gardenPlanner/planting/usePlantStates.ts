import { useCallback, useEffect, useMemo, useState } from 'react';
import { computePlantState, utcDay, type PhaseFacts, type PlantVisualState } from '../model/plantState';
import { listPlantStates, type PlantStateWire } from './plantStateApi';

/** A plant of the answer with the state the port computed at the current instant (GP-FR-192). */
export interface PlantStateView extends PlantStateWire {
  visual: PlantVisualState;
}

/** The calendar day rolls over at midnight UTC; a minute is fine-grained enough and cheap. */
const TICK_MS = 60_000;

/** The state only changes with the day (GP-FR-192 works on UTC calendar days), so only a new day recomputes it. */
const today = () => utcDay(new Date().toISOString());

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
  const [day, setDay] = useState(today);

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

  useEffect(() => {
    if (!enabled) return undefined;
    const timer = window.setInterval(() => setDay(today()), TICK_MS);
    const onVisible = () => {
      if (document.visibilityState === 'visible') setAttempt((value) => value + 1);
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [enabled]);

  const refresh = useCallback(() => setAttempt((value) => value + 1), []);
  const current = wires && wires.bedKey === bedKey ? wires : null;
  const states = useMemo(() => {
    if (!current) return {};
    // `day` is the clock: the state is recomputed when the answer or the day changes, not every minute.
    const now = `${day}T12:00:00Z`;
    return Object.fromEntries(
      current.items.map((wire): [string, PlantStateView] => [wire.plant_key, { ...wire, visual: visualOf(wire, now) }]),
    );
  }, [current, day]);
  const loadedAt = current?.loadedAt ?? null;
  return useMemo(() => ({ states, loadedAt, refresh }), [states, loadedAt, refresh]);
}
