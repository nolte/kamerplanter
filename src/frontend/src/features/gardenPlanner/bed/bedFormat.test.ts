import { describe, expect, it } from 'vitest';
import { isOverdue } from './bedFormat';

describe('isOverdue', () => {
  const now = new Date(2026, 5, 18, 15, 30);

  it('is false for a task due today, whatever the time of day', () => {
    expect(isOverdue(new Date(2026, 5, 18, 0, 0).toISOString(), now)).toBe(false);
    expect(isOverdue(new Date(2026, 5, 18, 9, 0).toISOString(), now)).toBe(false);
  });

  it('is true from the day after the due date', () => {
    expect(isOverdue(new Date(2026, 5, 17, 23, 59).toISOString(), now)).toBe(true);
  });

  it('is false for the future, nothing and nonsense', () => {
    expect(isOverdue(new Date(2026, 5, 19).toISOString(), now)).toBe(false);
    expect(isOverdue(null, now)).toBe(false);
    expect(isOverdue('not a date', now)).toBe(false);
  });
});
