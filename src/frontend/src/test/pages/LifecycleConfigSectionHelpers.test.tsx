import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { LifecycleConfig } from '@/api/types';

const getLifecycleConfig = vi.fn();
const updateLifecycleConfig = vi.fn();
const createLifecycleConfig = vi.fn();
vi.mock('@/api/endpoints/phases', () => ({
  getLifecycleConfig: (...args: unknown[]) => getLifecycleConfig(...args),
  listGrowthPhases: vi.fn().mockResolvedValue([]),
  createLifecycleConfig: (...args: unknown[]) => createLifecycleConfig(...args),
  updateLifecycleConfig: (...args: unknown[]) => updateLifecycleConfig(...args),
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
    // Derived server-side: perennial + cultivated-annual → grown as an annual.
    grown_as_annual: true,
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

describe('LifecycleConfigSection — helper texts & glossary tooltips (#633)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    getLifecycleConfig.mockReset();
    updateLifecycleConfig.mockReset();
    createLifecycleConfig.mockReset();
    getLifecycleConfig.mockResolvedValue(makeLifecycle());
    updateLifecycleConfig.mockResolvedValue(makeLifecycle());
  });

  it('renders plain-text helper texts for cycle type and both dormancy toggles', async () => {
    renderWithProviders(<LifecycleConfigSection speciesKey="sp-1" />, {
      store: createStoreWithExpertise('beginner'),
    });

    expect(await screen.findByText(i18n.t('pages.lifecycle.cycleTypeHelper'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.lifecycle.dormancyHelper'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.lifecycle.vernalizationHelper'))).toBeInTheDocument();
  });

  it('renders glossary help tooltips for the domain terms', async () => {
    renderWithProviders(<LifecycleConfigSection speciesKey="sp-1" />, {
      store: createStoreWithExpertise('beginner'),
    });

    expect(await screen.findByTestId('help-tooltip-icon-dormancy')).toBeInTheDocument();
    expect(screen.getByTestId('help-tooltip-icon-vernalization')).toBeInTheDocument();
    expect(screen.getByTestId('help-tooltip-icon-photoperiod')).toBeInTheDocument();
  });

  it('keeps both dormancy toggles as switches driven by the form state', async () => {
    renderWithProviders(<LifecycleConfigSection speciesKey="sp-1" />, {
      store: createStoreWithExpertise('beginner'),
    });

    expect(await screen.findByTestId('form-field-dormancy_required')).toBeInTheDocument();
    expect(screen.getByTestId('form-field-vernalization_required')).toBeInTheDocument();
  });
});
