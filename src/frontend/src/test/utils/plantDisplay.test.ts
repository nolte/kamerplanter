import { describe, it, expect } from 'vitest';
import {
  formatSpeciesNameWithScientific,
  getLocalizedCommonName,
  getSpeciesLabel,
  getSpeciesOptionLabel,
  getPlantDisplayName,
  getPlantLabel,
  normalizeNameLanguage,
  orderCommonNamesForLanguage,
  type PlantLike,
} from '@/utils/plantDisplay';

// As the API serves a seeded species (#2902): the flat list names English FIRST
// (species.yaml order), the language map says which name is which.
const speciesSummary = {
  scientific_name: 'Ocimum basilicum',
  common_names: ['Basil', 'Basilikum', 'Königskraut'],
  common_names_i18n: { de: ['Basilikum', 'Königskraut'], en: ['Basil'] },
};
const cultivarSummary = { name: 'Genovese' };

function plant(overrides: Partial<PlantLike> = {}): PlantLike {
  return {
    instance_id: 'BASIL-001',
    plant_name: null,
    species: null,
    cultivar: null,
    ...overrides,
  };
}

describe('getLocalizedCommonName (REQ-001, #2902)', () => {
  const leek = {
    scientific_name: 'Allium porrum',
    common_names: ['Leek', 'Lauch', 'Porree'],
    common_names_i18n: { de: ['Lauch', 'Porree'], en: ['Leek'] },
  };

  it('takes the first German name in the German UI, never the first list entry', () => {
    expect(getLocalizedCommonName(leek, 'de')).toBe('Lauch');
  });

  it('takes the first English name in the English UI', () => {
    expect(getLocalizedCommonName(leek, 'en')).toBe('Leek');
  });

  it('normalizes a region-tagged language (de-DE, en_GB)', () => {
    expect(getLocalizedCommonName(leek, 'de-DE')).toBe('Lauch');
    expect(getLocalizedCommonName(leek, 'en_GB')).toBe('Leek');
  });

  it('falls back to German when the UI language has no name', () => {
    expect(getLocalizedCommonName(leek, 'fr')).toBe('Lauch');
    expect(
      getLocalizedCommonName(
        { scientific_name: 'Pisum sativum', common_names: ['Erbse'], common_names_i18n: { de: ['Erbse'] } },
        'en',
      ),
    ).toBe('Erbse');
  });

  it('falls back to the scientific name when the map has neither the UI language nor German', () => {
    // English-only map in the German UI: the untagged list is not consulted, it would leak English.
    expect(
      getLocalizedCommonName(
        { scientific_name: 'Zamioculcas zamiifolia', common_names: ['ZZ plant'], common_names_i18n: { en: ['ZZ plant'] } },
        'de',
      ),
    ).toBe('Zamioculcas zamiifolia');
    // A map whose languages hold no name at all.
    expect(
      getLocalizedCommonName(
        { scientific_name: 'Allium porrum', common_names: ['Leek'], common_names_i18n: { de: [], en: ['  '] } },
        'de',
      ),
    ).toBe('Allium porrum');
  });

  it('takes the first common name when the species has no language map (tenant-created, CSV, adapters)', () => {
    const typedByUser = { scientific_name: 'Solanum lycopersicum', common_names: ['Ochsenherz-Tomate', 'Tomate'] };
    expect(getLocalizedCommonName(typedByUser, 'de')).toBe('Ochsenherz-Tomate');
    expect(getLocalizedCommonName({ ...typedByUser, common_names_i18n: {} }, 'en')).toBe('Ochsenherz-Tomate');
    expect(getLocalizedCommonName({ ...typedByUser, common_names_i18n: null }, 'de')).toBe('Ochsenherz-Tomate');
  });

  it('skips blank names and falls back to the scientific name without any name', () => {
    expect(getLocalizedCommonName({ scientific_name: 'Allium porrum', common_names: ['  ', 'Lauch'] }, 'de')).toBe(
      'Lauch',
    );
    expect(getLocalizedCommonName({ scientific_name: 'Allium porrum', common_names: [] }, 'de')).toBe('Allium porrum');
    expect(getLocalizedCommonName({ scientific_name: 'Allium porrum' }, 'de')).toBe('Allium porrum');
  });

  it('returns null when neither a common nor a scientific name is available', () => {
    expect(getLocalizedCommonName(null, 'de')).toBeNull();
    expect(getLocalizedCommonName({ scientific_name: null, common_names: [] }, 'de')).toBeNull();
  });
});

describe('normalizeNameLanguage', () => {
  it.each([
    ['de', 'de'],
    ['de-DE', 'de'],
    ['EN_us', 'en'],
    ['', 'de'],
    [null, 'de'],
    [undefined, 'de'],
  ])('maps %s to %s', (input, expected) => {
    expect(normalizeNameLanguage(input)).toBe(expected);
  });
});

describe('orderCommonNamesForLanguage', () => {
  it('lists the names of the UI language first and keeps every other name', () => {
    expect(orderCommonNamesForLanguage(speciesSummary, 'de')).toEqual(['Basilikum', 'Königskraut', 'Basil']);
    expect(orderCommonNamesForLanguage(speciesSummary, 'en')).toEqual(['Basil', 'Basilikum', 'Königskraut']);
  });

  it('keeps the stored order without a map', () => {
    expect(orderCommonNamesForLanguage({ common_names: ['B', 'A'] }, 'de')).toEqual(['B', 'A']);
  });
});

describe('option labels', () => {
  it('shows "Common (Scientific)" with the common name in the UI language', () => {
    expect(getSpeciesOptionLabel(speciesSummary, 'de')).toBe('Basilikum (Ocimum basilicum)');
    expect(getSpeciesOptionLabel(speciesSummary, 'en')).toBe('Basil (Ocimum basilicum)');
  });

  it('shows only the scientific name when there is no distinct common name', () => {
    expect(getSpeciesOptionLabel({ scientific_name: 'Ocimum basilicum', common_names: [] }, 'de')).toBe(
      'Ocimum basilicum',
    );
    expect(formatSpeciesNameWithScientific(null, 'Ocimum basilicum')).toBe('Ocimum basilicum');
    expect(formatSpeciesNameWithScientific('Basilikum', 'Ocimum basilicum')).toBe('Basilikum (Ocimum basilicum)');
  });
});

describe('getSpeciesLabel', () => {
  it('uses the common name of the UI language', () => {
    expect(getSpeciesLabel(speciesSummary, 'de')).toBe('Basilikum');
    expect(getSpeciesLabel(speciesSummary, 'en')).toBe('Basil');
  });

  it('falls back to the scientific name when no common names exist', () => {
    expect(getSpeciesLabel({ scientific_name: 'Ocimum basilicum', common_names: [] }, 'de')).toBe(
      'Ocimum basilicum',
    );
  });

  it('appends the cultivar with an en-dash', () => {
    expect(getSpeciesLabel(speciesSummary, 'de', cultivarSummary)).toBe('Basilikum – Genovese');
  });

  it('ignores a blank cultivar name', () => {
    expect(getSpeciesLabel(speciesSummary, 'de', { name: '  ' })).toBe('Basilikum');
  });

  it('returns null without species data', () => {
    expect(getSpeciesLabel(null, 'de')).toBeNull();
    expect(getSpeciesLabel(undefined, 'de')).toBeNull();
  });
});

describe('getPlantDisplayName', () => {
  it('uses plant_name when set', () => {
    expect(getPlantDisplayName(plant({ plant_name: 'Mein Basilikum' }), 'de')).toBe('Mein Basilikum');
  });

  it('prefers plant_name over species/cultivar', () => {
    expect(
      getPlantDisplayName(
        plant({ plant_name: 'Mein Basilikum', species: speciesSummary, cultivar: cultivarSummary }),
        'de',
      ),
    ).toBe('Mein Basilikum');
  });

  it('uses embedded species + cultivar when plant_name is missing', () => {
    expect(getPlantDisplayName(plant({ species: speciesSummary, cultivar: cultivarSummary }), 'de')).toBe(
      'Basilikum – Genovese',
    );
  });

  it('uses embedded species without cultivar, in the UI language', () => {
    expect(getPlantDisplayName(plant({ species: speciesSummary }), 'de')).toBe('Basilikum');
    expect(getPlantDisplayName(plant({ species: speciesSummary }), 'en')).toBe('Basil');
  });

  it('lets explicitly passed species/cultivar override embedded ones', () => {
    expect(
      getPlantDisplayName(
        plant({ species: speciesSummary }),
        'de',
        {
          scientific_name: 'Solanum lycopersicum',
          common_names: ['Tomato', 'Tomate'],
          common_names_i18n: { de: ['Tomate'], en: ['Tomato'] },
        },
        { name: 'San Marzano' },
      ),
    ).toBe('Tomate – San Marzano');
  });

  it('falls back to instance_id when nothing else is available', () => {
    expect(getPlantDisplayName(plant(), 'de')).toBe('BASIL-001');
  });

  it('treats a blank plant_name as unset', () => {
    expect(getPlantDisplayName(plant({ plant_name: '   ', species: speciesSummary }), 'de')).toBe('Basilikum');
  });
});

describe('getPlantLabel', () => {
  it('combines instance_id with the speaking name', () => {
    expect(getPlantLabel(plant({ species: speciesSummary, cultivar: cultivarSummary }), 'de')).toBe(
      'BASIL-001 (Basilikum – Genovese)',
    );
  });

  it('combines instance_id with a user-set plant_name', () => {
    expect(getPlantLabel(plant({ plant_name: 'Mein Basilikum' }), 'de')).toBe('BASIL-001 (Mein Basilikum)');
  });

  it('returns only the instance_id when no speaking name resolves', () => {
    expect(getPlantLabel(plant(), 'de')).toBe('BASIL-001');
  });

  it('avoids redundant parentheses when plant_name equals instance_id', () => {
    expect(getPlantLabel(plant({ plant_name: 'BASIL-001' }), 'de')).toBe('BASIL-001');
  });
});
