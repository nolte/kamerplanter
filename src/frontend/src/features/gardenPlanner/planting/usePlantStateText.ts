import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import type { AttentionCode, Lifecycle } from '../model/plantState';
import { formatBedDate } from '../bed/bedFormat';
import type { PlantMarkerState } from '../renderer/types';
import type { PlantStateView } from './usePlantStates';

const PREFIX = 'pages.gardenPlan.plantState';

const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;

/**
 * A stored day as a short local date. A date without a time is a calendar day, not an instant: it is shown as
 * that day in every time zone (UTC midnight formatted in UTC), where an instant keeps the viewer's zone.
 */
export function formatDay(value: string | null | undefined, language: string): string | null {
  if (!value) return null;
  if (!DATE_ONLY.test(value)) return formatBedDate(value, language);
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(language, { dateStyle: 'medium', timeZone: 'UTC' }).format(date);
}

export interface PlantInfoLine {
  key: string;
  text: string;
  /** The line is a reason to act: drawn emphasised (an overdue task, a finding). */
  alert?: boolean;
}

/** The bubble is one glance: at most this many lines (GP-FR-190). The least useful go first. */
export const MAX_INFO_LINES = 8;

/** How long a line survives the cut to {@link MAX_INFO_LINES}: a higher rank stays. */
const RANK: Record<string, number> = {
  eta: 1,
  harvested: 1,
  fed: 2,
  watered: 2,
  position: 3,
  harvest: 3,
  age: 4,
  phase: 5,
  task: 6,
};
const ATTENTION_RANK = 7;

function cutToLimit(lines: PlantInfoLine[]): PlantInfoLine[] {
  const rankOf = (line: PlantInfoLine) => RANK[line.key] ?? ATTENTION_RANK;
  const kept = [...lines];
  while (kept.length > MAX_INFO_LINES) {
    const lowest = Math.min(...kept.map(rankOf));
    kept.splice(kept.findIndex((line) => rankOf(line) === lowest), 1);
  }
  return kept;
}

export interface PlantStateText {
  lifecycle: (lifecycle: Lifecycle) => string;
  /** One attention reason in plain words ("2 Aufgaben überfällig"). */
  attention: (reason: AttentionCode, count: number, findingLabel?: string | null) => string;
  /** The name the plant goes by on the plan: species name, else scientific name, else the instance id. */
  name: (view: PlantStateView) => string;
  /** "Tomate, Blüte, 2 Aufgaben überfällig" - what a screen reader says for the marker (GP-UX-062). */
  ariaLabel: (view: PlantStateView) => string;
  /** What the renderer draws for the plant. */
  marker: (view: PlantStateView) => PlantMarkerState;
  /** The lines of the info bubble, empty ones left out, at most eight (GP-FR-190). */
  lines: (view: PlantStateView) => PlantInfoLine[];
}

/** All texts of the plant info and the marker label, from `pages.gardenPlan.plantState.*` (DE/EN). */
export function usePlantStateText(): PlantStateText {
  const { t, i18n } = useTranslation();
  return useMemo(() => {
    const language = i18n.language;
    const day = (value: string | null | undefined) => formatDay(value, language);
    const lifecycle = (value: Lifecycle) => t(`${PREFIX}.lifecycle.${value}`);
    const attention = (reason: AttentionCode, count: number, findingLabel?: string | null) => {
      if (reason === 'problem') {
        return findingLabel
          ? t(`${PREFIX}.attention.problem`, { label: findingLabel })
          : t(`${PREFIX}.attention.problemUnnamed`);
      }
      if (reason === 'overdue') return t(`${PREFIX}.attention.overdue`, { count });
      return t(`${PREFIX}.attention.${reason}`);
    };
    const name = (view: PlantStateView) => view.species_name || view.scientific_name || view.instance_id;
    const reasons = (view: PlantStateView) =>
      view.visual.attention.map((item) => attention(item.reason, item.count, view.finding_label));
    const ariaLabel = (view: PlantStateView) =>
      [
        name(view),
        view.phase?.name,
        view.visual.lifecycle === 'active' ? null : lifecycle(view.visual.lifecycle),
        ...reasons(view),
      ]
        .filter(Boolean)
        .join(', ');
    return {
      lifecycle,
      attention,
      name,
      ariaLabel,
      marker: (view) => ({
        lifecycle: view.visual.lifecycle,
        badge: view.visual.attention[0]?.reason ?? null,
        initial: name(view).charAt(0).toLocaleUpperCase(language),
        progress: view.visual.phase_progress?.fraction ?? null,
        ariaLabel: ariaLabel(view),
      }),
      lines: (view) => {
        const lines: PlantInfoLine[] = [];
        const progress = view.visual.phase_progress;
        if (view.phase?.name && progress) {
          lines.push({
            key: 'phase',
            text:
              progress.typical_d !== null
                ? t(`${PREFIX}.info.phase`, {
                    phase: view.phase.name,
                    elapsed: progress.elapsed_d,
                    typical: progress.typical_d,
                  })
                : t(`${PREFIX}.info.phaseOpen`, { phase: view.phase.name, elapsed: progress.elapsed_d }),
          });
          const eta = day(progress.next_phase_eta);
          if (eta) lines.push({ key: 'eta', text: t(`${PREFIX}.info.nextPhase`, { date: eta }) });
        }
        const planted = day(view.planted_on);
        if (planted) {
          const days = Math.max(
            0,
            Math.floor((Date.now() - Date.parse(`${view.planted_on.slice(0, 10)}T00:00:00Z`)) / 86_400_000),
          );
          lines.push({ key: 'age', text: t(`${PREFIX}.info.age`, { date: planted, days }) });
        }
        if (view.slot_id) lines.push({ key: 'position', text: t(`${PREFIX}.info.position`, { slot: view.slot_id }) });
        const watered = day(view.last_care.watering);
        if (watered) lines.push({ key: 'watered', text: t(`${PREFIX}.info.watered`, { date: watered }) });
        const fed = day(view.last_care.feeding);
        if (fed) lines.push({ key: 'fed', text: t(`${PREFIX}.info.fed`, { date: fed }) });
        if (view.next_task) {
          const due = day(view.next_task.due);
          lines.push({
            key: 'task',
            alert: view.next_task.due != null && view.next_task.due.slice(0, 10) < new Date().toISOString().slice(0, 10),
            text: due
              ? t(`${PREFIX}.info.nextTask`, { name: view.next_task.name, date: due })
              : t(`${PREFIX}.info.nextTaskUndated`, { name: view.next_task.name }),
          });
        }
        for (const item of view.visual.attention) {
          lines.push({
            key: `attention-${item.reason}`,
            alert: item.reason === 'problem' || item.reason === 'overdue' || item.reason === 'frost',
            text: attention(item.reason, item.count, view.finding_label),
          });
        }
        const readyFrom = day(view.visual.harvest_ready_from);
        if (view.visual.harvest_ready && readyFrom) {
          lines.push({ key: 'harvest', text: t(`${PREFIX}.info.harvestReadyFrom`, { date: readyFrom }) });
        }
        if (view.harvest.harvested_total_g != null) {
          lines.push({
            key: 'harvested',
            text: t(`${PREFIX}.info.harvestedTotal`, {
              grams: new Intl.NumberFormat(language, { maximumFractionDigits: 1 }).format(view.harvest.harvested_total_g),
            }),
          });
        }
        return cutToLimit(lines);
      },
    };
  }, [t, i18n.language]);
}
