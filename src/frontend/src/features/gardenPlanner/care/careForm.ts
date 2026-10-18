/**
 * The state of the short care form and its translation into the wire payload (REQ-053 GP-FR-084,
 * GP-FR-085). Pure, so the dialog tests can pin the rules without rendering.
 */
import { formKindOf, UNITS_BY_KIND, type FormKind } from './careCategories';
import type { CareEventBody, CareUnit, CompletionPayload, FertilizerRef } from './careTypes';

const MS_PER_DAY = 86_400_000;
/** GP-FR-085: backdating reaches a year, never into the future. */
export const MAX_BACKDATE_DAYS = 365;
const NOTE_MAX = 2000;
const TEXT_MAX = 200;

/** Everything the short form can hold; fields a category does not ask for stay empty. */
export interface CareFormState {
  /** `datetime-local` value (`YYYY-MM-DDTHH:mm`, local time). */
  performedAt: string;
  /** Whether the user changed the instant; an untouched "now" is left to the server. */
  performedAtTouched: boolean;
  quantity: string;
  unit: CareUnit | '';
  /** Water source, material or cover; a code or free text. */
  material: string;
  productLabel: string;
  product: FertilizerRef | null;
  note: string;
}

export type FormErrors = Partial<Record<'performedAt' | 'quantity' | 'material' | 'productLabel' | 'note', string>>;

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

/** A `datetime-local` value for `date` in local time. */
export function toLocalInput(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/**
 * The earliest instant the field takes: a year back, rounded UP to the next full minute, because the input
 * has no seconds and a value rounded down would lie before the server's limit (GP-FR-085).
 */
function earliestAllowed(now: Date): Date {
  const earliest = new Date(now.getTime() - MAX_BACKDATE_DAYS * MS_PER_DAY);
  earliest.setSeconds(0, 0);
  return earliest.getTime() < now.getTime() - MAX_BACKDATE_DAYS * MS_PER_DAY
    ? new Date(earliest.getTime() + 60_000)
    : earliest;
}

/** The bounds of the instant field (GP-FR-085), for the input's `min` and `max`. */
export function performedAtBounds(now: Date): { min: string; max: string } {
  return { min: toLocalInput(earliestAllowed(now)), max: toLocalInput(now) };
}

export function emptyForm(now: Date = new Date()): CareFormState {
  return {
    performedAt: toLocalInput(now),
    performedAtTouched: false,
    quantity: '',
    unit: '',
    material: '',
    productLabel: '',
    product: null,
    note: '',
  };
}

/** The default unit of a form kind (the first it offers), or empty. */
export function defaultUnit(kind: FormKind): CareUnit | '' {
  return UNITS_BY_KIND[kind][0] ?? '';
}

/** Parse a decimal typed with a comma or a point; `null` when it is not a number. */
export function parseQuantity(text: string): number | null {
  const trimmed = text.trim().replace(',', '.');
  if (trimmed === '') return null;
  const value = Number(trimmed);
  return Number.isFinite(value) ? value : null;
}

/** `future`, `tooOld` or `invalid` when the instant breaks GP-FR-085; `null` when it is fine. */
export function performedAtProblem(value: string, now: Date): 'future' | 'tooOld' | 'invalid' | null {
  const at = new Date(value);
  if (Number.isNaN(at.getTime())) return 'invalid';
  if (at.getTime() > now.getTime()) return 'future';
  if (at.getTime() < earliestAllowed(now).getTime()) return 'tooOld';
  return null;
}

/** Field problems as i18n keys below `pages.bed.care.errors`; an empty object means the form may be sent. */
export function validateForm(state: CareFormState, now: Date): FormErrors {
  const errors: FormErrors = {};
  if (state.performedAtTouched) {
    const problem = performedAtProblem(state.performedAt, now);
    if (problem) errors.performedAt = problem;
  }
  if (state.quantity.trim() !== '') {
    const quantity = parseQuantity(state.quantity);
    if (quantity === null || quantity < 0) errors.quantity = 'quantity';
  }
  if (state.material.length > TEXT_MAX) errors.material = 'tooLong';
  if (state.productLabel.length > TEXT_MAX) errors.productLabel = 'tooLong';
  if (state.note.length > NOTE_MAX) errors.note = 'tooLong';
  return errors;
}

interface Fields {
  performed_at?: string;
  product_ref?: FertilizerRef;
  product_label?: string;
  quantity?: number;
  unit?: CareUnit;
  material?: string;
}

/** The care fields the category's form asks for; anything else typed earlier is dropped. */
function careFields(state: CareFormState, category: string): Fields {
  const kind = formKindOf(category);
  const fields: Fields = {};
  if (state.performedAtTouched) fields.performed_at = new Date(state.performedAt).toISOString();

  if (UNITS_BY_KIND[kind].length > 0) {
    const quantity = parseQuantity(state.quantity);
    const unit = state.unit !== '' ? state.unit : defaultUnit(kind);
    if (quantity !== null && unit !== '') {
      fields.quantity = quantity;
      fields.unit = unit;
    }
  }
  const material = state.material.trim();
  if (material !== '' && (kind === 'watering' || kind === 'amendment' || kind === 'mulching' || kind === 'cover')) {
    fields.material = material;
  }
  if (kind === 'feeding') {
    if (state.product) fields.product_ref = state.product;
    const label = state.productLabel.trim();
    if (label !== '') fields.product_label = label;
  }
  return fields;
}

/** Body of `POST /tasks/{key}/complete` and `POST /tasks/batch/status` (GP-FR-083/088). */
export function buildCompletionPayload(state: CareFormState, category: string): CompletionPayload {
  const payload: CompletionPayload = careFields(state, category);
  const note = state.note.trim();
  if (note !== '') payload.completion_notes = note;
  return payload;
}

/** Body of `POST /care-events` (GP-FR-090); `summary` is required, so it falls back to the category label. */
export function buildLogBody(
  state: CareFormState,
  category: string,
  locationKey: string,
  summary: string,
  now: Date,
): CareEventBody {
  const fields = careFields(state, category);
  const note = state.note.trim();
  return {
    location_key: locationKey,
    category,
    summary: (category === 'note' && note !== '' ? note : summary).slice(0, 500),
    ...fields,
    performed_at: fields.performed_at ?? now.toISOString(),
    ...(note !== '' && category !== 'note' ? { observed_outcome: note } : {}),
  };
}
