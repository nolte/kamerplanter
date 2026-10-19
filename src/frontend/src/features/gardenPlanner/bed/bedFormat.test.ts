import { describe, expect, it } from 'vitest';
import { isOverdue } from './bedFormat';

/** The boundary cases live in the shared vectors (`model/overdue.vectors.test.ts`); this pins the re-export. */
describe('isOverdue (bed list column)', () => {
  const now = new Date('2026-06-18T15:30:00Z');

  it('is false for a task due today, whatever the time of day (UTC)', () => {
    expect(isOverdue('2026-06-18T00:00:00Z', now)).toBe(false);
    expect(isOverdue('2026-06-18T23:59:00Z', now)).toBe(false);
  });

  it('is true from the UTC day after the due date', () => {
    expect(isOverdue('2026-06-17T23:59:59Z', now)).toBe(true);
  });

  it('is false for the future, nothing and nonsense', () => {
    expect(isOverdue('2026-06-19T00:00:00Z', now)).toBe(false);
    expect(isOverdue(null, now)).toBe(false);
    expect(isOverdue('not a date', now)).toBe(false);
  });
});
