import { describe, it, expect } from 'vitest';
import {
  getSpeciesLabel,
  getPlantDisplayName,
  getPlantLabel,
  type PlantLike,
} from '@/utils/plantDisplay';

const speciesSummary = {
  scientific_name: 'Ocimum basilicum',
  common_names: ['Basilikum', 'Basil'],
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

describe('getSpeciesLabel', () => {
  it('prefers the first common name', () => {
    expect(getSpeciesLabel(speciesSummary)).toBe('Basilikum');
  });

  it('falls back to the scientific name when no common names exist', () => {
    expect(getSpeciesLabel({ scientific_name: 'Ocimum basilicum', common_names: [] })).toBe(
      'Ocimum basilicum',
    );
  });

  it('appends the cultivar with an en-dash', () => {
    expect(getSpeciesLabel(speciesSummary, cultivarSummary)).toBe('Basilikum – Genovese');
  });

  it('ignores a blank cultivar name', () => {
    expect(getSpeciesLabel(speciesSummary, { name: '  ' })).toBe('Basilikum');
  });

  it('returns null without species data', () => {
    expect(getSpeciesLabel(null)).toBeNull();
    expect(getSpeciesLabel(undefined)).toBeNull();
  });
});

describe('getPlantDisplayName', () => {
  it('uses plant_name when set', () => {
    expect(getPlantDisplayName(plant({ plant_name: 'Mein Basilikum' }))).toBe('Mein Basilikum');
  });

  it('prefers plant_name over species/cultivar', () => {
    expect(
      getPlantDisplayName(
        plant({ plant_name: 'Mein Basilikum', species: speciesSummary, cultivar: cultivarSummary }),
      ),
    ).toBe('Mein Basilikum');
  });

  it('uses embedded species + cultivar when plant_name is missing', () => {
    expect(getPlantDisplayName(plant({ species: speciesSummary, cultivar: cultivarSummary }))).toBe(
      'Basilikum – Genovese',
    );
  });

  it('uses embedded species without cultivar', () => {
    expect(getPlantDisplayName(plant({ species: speciesSummary }))).toBe('Basilikum');
  });

  it('lets explicitly passed species/cultivar override embedded ones', () => {
    expect(
      getPlantDisplayName(
        plant({ species: speciesSummary }),
        { scientific_name: 'Solanum lycopersicum', common_names: ['Tomate'] },
        { name: 'San Marzano' },
      ),
    ).toBe('Tomate – San Marzano');
  });

  it('falls back to instance_id when nothing else is available', () => {
    expect(getPlantDisplayName(plant())).toBe('BASIL-001');
  });

  it('treats a blank plant_name as unset', () => {
    expect(getPlantDisplayName(plant({ plant_name: '   ', species: speciesSummary }))).toBe(
      'Basilikum',
    );
  });
});

describe('getPlantLabel', () => {
  it('combines instance_id with the speaking name', () => {
    expect(getPlantLabel(plant({ species: speciesSummary, cultivar: cultivarSummary }))).toBe(
      'BASIL-001 (Basilikum – Genovese)',
    );
  });

  it('combines instance_id with a user-set plant_name', () => {
    expect(getPlantLabel(plant({ plant_name: 'Mein Basilikum' }))).toBe(
      'BASIL-001 (Mein Basilikum)',
    );
  });

  it('returns only the instance_id when no speaking name resolves', () => {
    expect(getPlantLabel(plant())).toBe('BASIL-001');
  });

  it('avoids redundant parentheses when plant_name equals instance_id', () => {
    expect(getPlantLabel(plant({ plant_name: 'BASIL-001' }))).toBe('BASIL-001');
  });
});
