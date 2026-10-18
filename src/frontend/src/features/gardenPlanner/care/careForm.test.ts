/**
 * The short care form (REQ-053 GP-FR-084/085): which fields reach the wire for which category, that an
 * empty form is valid, and the backdating window of a year.
 */
import { describe, expect, it } from 'vitest';
import {
  buildCompletionPayload,
  buildLogBody,
  defaultUnit,
  emptyForm,
  performedAtBounds,
  performedAtProblem,
  validateForm,
  type CareFormState,
} from './careForm';
import { formKindOf } from './careCategories';

const NOW = new Date(2026, 5, 14, 18, 30);

function form(category: string, patch: Partial<CareFormState> = {}): CareFormState {
  return { ...emptyForm(NOW), unit: defaultUnit(formKindOf(category)), ...patch };
}

describe('buildCompletionPayload', () => {
  it('sends nothing for an untouched form (a tap on "Done" is valid, GP-FR-084)', () => {
    expect(buildCompletionPayload(form('watering'), 'watering')).toEqual({});
    expect(validateForm(form('watering'), NOW)).toEqual({});
  });

  it('watering: litres and source; the default unit is litres', () => {
    const payload = buildCompletionPayload(form('watering', { quantity: '12,5', material: 'rainwater' }), 'watering');
    expect(payload).toEqual({ quantity: 12.5, unit: 'l', material: 'rainwater' });
  });

  it('feeding: product reference, label, amount and unit', () => {
    const payload = buildCompletionPayload(
      form('feeding', {
        product: { kind: 'fertilizer', key: 'fert_1' },
        productLabel: 'Nettle tea',
        quantity: '2',
        unit: 'l_per_m2',
      }),
      'feeding',
    );
    expect(payload).toEqual({
      product_ref: { kind: 'fertilizer', key: 'fert_1' },
      product_label: 'Nettle tea',
      quantity: 2,
      unit: 'l_per_m2',
    });
  });

  it('mulching: material and thickness in centimetres', () => {
    expect(buildCompletionPayload(form('mulching', { material: 'straw', quantity: '5' }), 'mulching')).toEqual({
      material: 'straw',
      quantity: 5,
      unit: 'cm',
    });
  });

  it('any other category: the note only; fields typed under another category are dropped', () => {
    const payload = buildCompletionPayload(
      form('weeding', { note: '  weeded the corner ', quantity: '3', material: 'straw', productLabel: 'x' }),
      'weeding',
    );
    expect(payload).toEqual({ completion_notes: 'weeded the corner' });
  });

  it('leaves the instant to the server until the user changes it', () => {
    expect(buildCompletionPayload(form('weeding'), 'weeding')).not.toHaveProperty('performed_at');
    const touched = form('weeding', { performedAt: '2026-06-10T08:00', performedAtTouched: true });
    expect(buildCompletionPayload(touched, 'weeding').performed_at).toBe(new Date(2026, 5, 10, 8, 0).toISOString());
  });
});

describe('buildLogBody', () => {
  it('uses the category label as the summary and the note as the outcome', () => {
    const body = buildLogBody(form('mulching', { note: 'before the rain', material: 'straw' }), 'mulching', 'loc_b03', 'Mulching', NOW);
    expect(body).toMatchObject({
      location_key: 'loc_b03',
      category: 'mulching',
      summary: 'Mulching',
      observed_outcome: 'before the rain',
      material: 'straw',
      performed_at: NOW.toISOString(),
    });
  });

  it('a free note is its own summary', () => {
    const body = buildLogBody(form('note', { note: 'First seedlings' }), 'note', 'loc_b03', 'Note', NOW);
    expect(body.summary).toBe('First seedlings');
    expect(body).not.toHaveProperty('observed_outcome');
  });
});

describe('the instant (GP-FR-085)', () => {
  it('allows now and a day 365 days back, refuses the future and a day beyond the year', () => {
    expect(performedAtProblem('2026-06-14T18:30', NOW)).toBeNull();
    expect(performedAtProblem('2025-06-14T18:30', NOW)).toBeNull();
    expect(performedAtProblem('2026-06-14T18:31', NOW)).toBe('future');
    expect(performedAtProblem('2025-06-14T18:29', NOW)).toBe('tooOld');
    expect(performedAtProblem('', NOW)).toBe('invalid');
  });

  it('rounds the lower bound up to the minute: a value the input offers is a value the validator takes', () => {
    const withSeconds = new Date(2026, 5, 14, 18, 30, 42);
    // The exact limit is 18:30:42 a year back; the input has no seconds, so its first value is 18:31.
    expect(performedAtBounds(withSeconds).min).toBe('2025-06-14T18:31');
    expect(performedAtProblem('2025-06-14T18:31', withSeconds)).toBeNull();
    expect(performedAtProblem('2025-06-14T18:30', withSeconds)).toBe('tooOld');
  });

  it('reports the problem only once the user has touched the field', () => {
    const untouched = form('watering', { performedAt: '2030-01-01T00:00' });
    expect(validateForm(untouched, NOW)).toEqual({});
    expect(validateForm({ ...untouched, performedAtTouched: true }, NOW)).toEqual({ performedAt: 'future' });
  });

  it('bounds the input to the same window', () => {
    expect(performedAtBounds(NOW)).toEqual({ min: '2025-06-14T18:30', max: '2026-06-14T18:30' });
  });
});

describe('validateForm', () => {
  it('refuses a negative or non-numeric amount', () => {
    expect(validateForm(form('watering', { quantity: '-1' }), NOW)).toEqual({ quantity: 'quantity' });
    expect(validateForm(form('watering', { quantity: 'abc' }), NOW)).toEqual({ quantity: 'quantity' });
    expect(validateForm(form('watering', { quantity: '0' }), NOW)).toEqual({});
  });
});
