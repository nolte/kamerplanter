import { screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { LifecycleConfig } from '@/api/types';

const getLifecycleConfig = vi.fn();
vi.mock('@/api/endpoints/phases', () => ({
  getLifecycleConfig: (...args: unknown[]) => getLifecycleConfig(...args),
  listGrowthPhases: vi.fn().mockResolvedValue([]),
  createLifecycleConfig: vi.fn(),
  updateLifecycleConfig: vi.fn(),
}));
vi.mock('@/api/endpoints/phaseSequences', () => ({
  getSpeciesPhaseSequence: vi.fn().mockResolvedValue(null),
}));

import LifecycleConfigSection from '@/pages/pflanzen/LifecycleConfigSection';
import { createStoreWithExpertise, renderWithProviders } from '../helpers';

function makeLifecycle(overrides: Partial<LifecycleConfig> = {}): LifecycleConfig {
  return {
    key: 'lc-1',
    species_key: 'sp-1',
    cycle_type: 'perennial',
    cultivation_cycle_type: 'annual',
    flowering_strategy: 'polycarpic',
    typical_lifespan_years: 10,
    dormancy_required: false,
    vernalization_required: false,
    vernalization_min_days: null,
    photoperiod_type: 'day_neutral',
    critical_day_length_hours: null,
    phase_sequence_key: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

describe('LifecycleConfigSection — Phase A fields', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    getLifecycleConfig.mockResolvedValue(makeLifecycle());
  });

  it('renders cultivation_cycle_type and flowering_strategy for an expert', async () => {
    renderWithProviders(<LifecycleConfigSection speciesKey="sp-1" />, {
      store: createStoreWithExpertise('expert'),
    });

    // cultivation_cycle_type (intermediate)
    const cct = await screen.findByTestId('form-field-cultivation_cycle_type');
    expect(within(cct).getByDisplayValue('annual')).toBeInTheDocument();

    // flowering_strategy (expert-only)
    const fs = screen.getByTestId('form-field-flowering_strategy');
    expect(within(fs).getByDisplayValue('polycarpic')).toBeInTheDocument();
  });

  it('hides the expert-only flowering_strategy field from a beginner', async () => {
    renderWithProviders(<LifecycleConfigSection speciesKey="sp-1" />, {
      store: createStoreWithExpertise('beginner'),
    });

    // cycle_type is always present (ungated)
    await screen.findByTestId('form-field-cycle_type');
    expect(screen.queryByTestId('form-field-flowering_strategy')).toBeNull();
    expect(screen.queryByTestId('form-field-cultivation_cycle_type')).toBeNull();
  });
});
