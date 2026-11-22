/**
 * Turns the history of the plan slice into the one sentence the live region should say next
 * (REQ-053 GP-NFR-022/070): a finished action, an undo or a redo. A load, a save or a selection
 * change says nothing here - the focus and the controls announce themselves.
 *
 * The sentence is derived while rendering (the documented "adjust state on a change" pattern), so
 * there is no effect between the store and the region.
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { PlanModel } from '../model/planModel';
import type { HistoryEntry } from '../state/gardenPlanSlice';
import { announceAction, type Translate } from './announce';

interface Seen {
  plan: PlanModel;
  pastLength: number;
  lastId: number | null;
  lastLabel: string | null;
  futureTopId: number | null;
}

const topOf = (entries: readonly HistoryEntry[]): HistoryEntry | null =>
  entries.length > 0 ? entries[entries.length - 1] : null;

export function useAnnouncement(
  plan: PlanModel,
  past: readonly HistoryEntry[],
  future: readonly HistoryEntry[],
  fallbackName: string,
): string {
  const { t, i18n } = useTranslation();
  const format = useMemo(() => {
    const numbers = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 });
    return (value: number) => numbers.format(value);
  }, [i18n.language]);
  const last = topOf(past);
  const futureTop = topOf(future);
  const [seen, setSeen] = useState<Seen>({
    plan,
    pastLength: past.length,
    lastId: last?.id ?? null,
    lastLabel: last?.label ?? null,
    futureTopId: futureTop?.id ?? null,
  });
  const [message, setMessage] = useState('');

  const changed = (last?.id ?? null) !== seen.lastId || past.length !== seen.pastLength;
  if (changed) {
    const prefix = 'pages.gardenPlan.editor.liveRegion';
    const say: Translate = (key, options) => String(t(key, (options ?? {}) as never));
    let next = '';
    if (last !== null && past.length >= seen.pastLength && last.id !== seen.lastId) {
      next =
        last.id === seen.futureTopId
          ? say(`${prefix}.redone`)
          : announceAction(last, plan, seen.plan, say, format, fallbackName);
    } else if (past.length < seen.pastLength && futureTop !== null) {
      const action = seen.lastLabel ? say(seen.lastLabel) : '';
      next = action ? say(`${prefix}.undoneAction`, { action }) : say(`${prefix}.undone`);
    }
    setSeen({
      plan,
      pastLength: past.length,
      lastId: last?.id ?? null,
      lastLabel: last?.label ?? null,
      futureTopId: futureTop?.id ?? null,
    });
    if (next !== '') setMessage(next);
  } else if (seen.plan !== plan || seen.futureTopId !== (futureTop?.id ?? null)) {
    setSeen({ ...seen, plan, futureTopId: futureTop?.id ?? null });
  }
  return message;
}
