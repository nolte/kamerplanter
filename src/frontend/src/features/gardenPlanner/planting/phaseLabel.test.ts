/** The growth phase in the reader's language, never the stored English name (#2764: "Phase: Seedling"). */
import { describe, expect, it } from 'vitest';
import i18n from '@/i18n/i18n';
import { phaseKeyOf, phaseLabel } from './phaseLabel';

describe('phaseLabel', () => {
  const de = i18n.getFixedT('de');

  it('words a known phase in German, whatever the case of the stored name', () => {
    expect(phaseLabel(de, 'Seedling')).toBe('Sämling');
    expect(phaseLabel(de, 'flowering')).toBe('Blüte');
  });

  it('keeps a phase the catalogue does not know as it is stored', () => {
    expect(phaseLabel(de, 'Bud swell')).toBe('Bud swell');
    expect(phaseKeyOf(' Bud-swell ')).toBe('bud_swell');
  });
});
