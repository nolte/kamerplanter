/**
 * Wording helpers of the history lists (REQ-053 GP-FR-102). Pure: they take the `t` function and the
 * wire value and return text, so the rows and their tests share them.
 */
import type { TFunction } from 'i18next';
import { isProtocolCategory } from './historyFilters';
import type { CareEventLine, HistoryItem } from './historyTypes';

/** The name of a care category: protocol entries have their own wording, tasks use the shared enum. */
export function categoryLabel(t: TFunction, category: string): string {
  return isProtocolCategory(category)
    ? t(`pages.bed.history.category.${category}`)
    : t(`enums.taskCategory.${category}`, { defaultValue: category });
}

/** `2 l`, `150 g/m²`, ...; empty when the line names no amount. */
export function formatQuantity(t: TFunction, line: Pick<CareEventLine, 'quantity' | 'unit'>): string {
  if (line.quantity === null) return '';
  const amount = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(line.quantity);
  return line.unit ? `${amount} ${t(`enums.careUnit.${line.unit}`, { defaultValue: line.unit })}` : amount;
}

/** What the grower did, in one line; a derived planting event has no summary of its own. */
export function itemHeadline(t: TFunction, item: HistoryItem): string {
  switch (item.kind) {
    case 'care_event':
      return item.care_event?.summary ?? categoryLabel(t, item.category);
    case 'plant_planted':
      return t('pages.bed.history.event.plantPlanted', { name: item.plant_name ?? item.plant_key ?? '' });
    case 'plant_removed':
      return item.termination_type
        ? t('pages.bed.history.event.plantRemovedHow', {
            name: item.plant_name ?? item.plant_key ?? '',
            how: t(`pages.bed.history.termination.${item.termination_type}`, { defaultValue: item.termination_type }),
          })
        : t('pages.bed.history.event.plantRemoved', { name: item.plant_name ?? item.plant_key ?? '' });
    case 'run_started':
      return t('pages.bed.history.event.runStarted', { name: item.run_name ?? '' });
    case 'run_completed':
      return t(
        item.run_status === 'cancelled' ? 'pages.bed.history.event.runCancelled' : 'pages.bed.history.event.runCompleted',
        { name: item.run_name ?? '' },
      );
  }
}

/** A care line of the tenant-wide log as a history item (the list component shows both). */
export function careLineToItem(line: CareEventLine): HistoryItem {
  return {
    id: `care:${line.key}`,
    kind: 'care_event',
    at: line.performed_at,
    category: line.category,
    care_event: line,
    plant_key: null,
    species_key: null,
    plant_name: null,
    termination_type: null,
    run_key: null,
    run_name: null,
    run_status: null,
  };
}
