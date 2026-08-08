import { describe, it, expect, beforeEach } from 'vitest';
import { z } from 'zod';
import i18n from 'i18next';
import '@/i18n';

/**
 * #1016 — the global error map (registered from `@/i18n`) must translate zod's
 * built-in constraint messages so a bare constraint never renders an English
 * default in the German UI. These parse against real schemas rather than calling
 * the map directly, so they prove the `z.config` registration is live.
 */
describe('global zod error map', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  function messageFor(schema: z.ZodType, value: unknown): string {
    const result = schema.safeParse(value);
    expect(result.success).toBe(false);
    return result.error!.issues[0].message;
  }

  it('translates gt(0) instead of the English "Too small" default', () => {
    // The exact case behind #1016: WateringLogCreateDialog volume_liters.
    expect(messageFor(z.number().gt(0), 0)).toBe(
      i18n.t('validation.numberGt', { minimum: 0 }),
    );
    // And it is German, not zod's default.
    expect(messageFor(z.number().gt(0), 0)).not.toMatch(/Too small|expected number/i);
  });

  it('reports a cleared numeric field as required, not "expected number, received null"', () => {
    expect(messageFor(z.number().gt(0), null)).toBe(i18n.t('validation.required'));
  });

  it('translates string min(1) as required', () => {
    expect(messageFor(z.string().min(1), '')).toBe(i18n.t('validation.required'));
  });

  it('translates max on a number', () => {
    expect(messageFor(z.number().max(14), 20)).toBe(
      i18n.t('validation.numberMax', { maximum: 14 }),
    );
  });

  it('translates email format', () => {
    expect(messageFor(z.string().email(), 'nope')).toBe(i18n.t('validation.email'));
  });

  it('honours an inline message rather than the global map', () => {
    expect(messageFor(z.string().min(1, 'Pflicht!'), '')).toBe('Pflicht!');
  });

  it('switches language with i18n', () => {
    i18n.changeLanguage('en');
    expect(messageFor(z.number().gt(0), 0)).toBe('Must be greater than 0.');
    i18n.changeLanguage('de');
  });
});
