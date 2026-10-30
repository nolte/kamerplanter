/**
 * The zone texts (REQ-053 WP 7.6 / 7.7): every error key the editor can show names a text in DE and EN, and the
 * two locales carry the same keys below `pages.gardenPlan.editor.zones`.
 */
import { describe, expect, it } from 'vitest';
import { ApiError } from '@/api/errors';
import { deFull as de, enFull as en } from '@/test/i18nTestResources';
import { errorKey } from './ZoneEditor';

const ZONES = ['pages', 'gardenPlan', 'editor', 'zones'];

function at(locale: unknown, path: readonly string[]): unknown {
  return path.reduce<unknown>((node, key) => (node as Record<string, unknown> | undefined)?.[key], locale);
}

function leaves(node: unknown, prefix = ''): string[] {
  if (typeof node !== 'object' || node === null) return [prefix];
  return Object.entries(node).flatMap(([key, value]) => leaves(value, prefix === '' ? key : `${prefix}.${key}`));
}

const apiError = (statusCode: number, code: string) =>
  new ApiError({ error_id: 'e', error_code: code, message: 'x', details: [], timestamp: '', path: '', method: 'POST' }, statusCode);

describe('zone texts', () => {
  it.each([
    [apiError(403, 'x')],
    [apiError(404, 'x')],
    [apiError(409, 'x')],
    [apiError(429, 'x')],
    [apiError(422, 'reference.not_found')],
    [apiError(422, 'irrigation_zone.no_beds')],
    [apiError(422, 'irrigation_zone.quota_exceeded')],
    [apiError(422, 'x')],
    [apiError(500, 'x')],
    [new Error('network')],
  ])('names a DE and an EN text for every error key the editor shows (%#)', (failure) => {
    const key = errorKey(failure);
    expect(typeof at(de, [...ZONES, 'errors', key])).toBe('string');
    expect(typeof at(en, [...ZONES, 'errors', key])).toBe('string');
  });

  it('carries the same keys in DE and EN', () => {
    expect(leaves(at(de, ZONES)).sort()).toEqual(leaves(at(en, ZONES)).sort());
  });
});
