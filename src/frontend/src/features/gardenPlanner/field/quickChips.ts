/**
 * The quick protocol of field mode (REQ-053 GP-UX-029, GP-FR-090, F-03): six chips in the bed sheet.
 * Three write a `care_event` with one tap; "harvested" and "note" open the short form (a quantity, a
 * text), "planted" opens the quick-planting shortcut (GP-UX-027). Pure, so the order and the bodies are
 * pinned without rendering.
 */
import type { CareEventBody } from '../care/careTypes';

export type QuickChipId = 'watering' | 'harvest' | 'sowing' | 'weeding' | 'planted' | 'note';

export interface QuickChip {
  id: QuickChipId;
  /**
   * `log`: one tap is one `care_event` of `category`; `form`: the short form of `category` opens;
   * `planting`: the quick-planting dialog opens.
   */
  action: 'log' | 'form' | 'planting';
  /** The care event category; `null` for the planting shortcut (the server logs the planting itself). */
  category: string | null;
}

/** The six chips in the order of the spec: Gegossen · Geerntet · Gesät · Gejätet/Gemulcht · Gepflanzt · Notiz. */
export const QUICK_CHIPS: readonly QuickChip[] = [
  { id: 'watering', action: 'log', category: 'watering' },
  { id: 'harvest', action: 'form', category: 'harvest' },
  { id: 'sowing', action: 'log', category: 'sowing' },
  // GP-ACC-048: "Gejätet/Gemulcht" is one tap and writes `weeding`; mulching with a material goes through the care tab.
  { id: 'weeding', action: 'log', category: 'weeding' },
  { id: 'planted', action: 'planting', category: null },
  { id: 'note', action: 'form', category: 'note' },
];

/**
 * The body of a one-tap chip: the bed, the category, its label as the summary (required by the server)
 * and the instant of the tap. `trigger` is not sent - the server sets `manual` (SR-009).
 */
export function quickLogBody(locationKey: string, category: string, summary: string, now: Date): CareEventBody {
  return {
    location_key: locationKey,
    category,
    summary: summary.slice(0, 500),
    performed_at: now.toISOString(),
  };
}
