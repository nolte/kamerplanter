import i18next from 'i18next';
import { describe, expect, it } from 'vitest';
import { itemHeadline } from './historyFormat';
import { careItem } from './historyTestKit';

/** The headline of a history line (GP-FR-102); a position correction is worded by the client (#2514). */
async function translator(lng: 'de' | 'en') {
  const pages = (await import(`../../../i18n/locales/${lng}/pages.json`)).default as Record<string, unknown>;
  const instance = i18next.createInstance();
  await instance.init({ lng, resources: { [lng]: { translation: pages } }, interpolation: { escapeValue: false } });
  return instance.t.bind(instance);
}

const SERVER_SUMMARY = 'Position corrected (BED_001)';

describe('itemHeadline: position_corrected (#2514)', () => {
  const corrected = careItem('p1', {
    category: 'position_corrected',
    summary: SERVER_SUMMARY,
    plant_keys: ['pl_1'],
    plant_names: ["Tomato 'Black Krim' #3"],
  });

  it('names the plant in German, not the slot of the stored English summary', async () => {
    const t = await translator('de');
    expect(itemHeadline(t, corrected)).toBe("Position korrigiert: Tomato 'Black Krim' #3");
  });

  it('names the plant in English', async () => {
    const t = await translator('en');
    expect(itemHeadline(t, corrected)).toBe("Position corrected: Tomato 'Black Krim' #3");
  });

  it('falls back to a line without a name when the plant is gone, never to the slot id', async () => {
    const gone = careItem('p2', { category: 'position_corrected', summary: SERVER_SUMMARY, plant_keys: ['pl_gone'] });
    const de = await translator('de');
    const en = await translator('en');
    expect(itemHeadline(de, gone)).toBe('Position einer Pflanze korrigiert');
    expect(itemHeadline(en, gone)).toBe('Position of a plant corrected');
  });

  it('keeps the stored summary of every other care entry', async () => {
    const t = await translator('de');
    expect(itemHeadline(t, careItem('w1', { summary: 'Tomaten gegossen', plant_names: ['TOM-1'] }))).toBe('Tomaten gegossen');
  });
});
