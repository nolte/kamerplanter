import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
    getLifecycleConfig.mockReset();
    updateLifecycleConfig.mockReset();
    createLifecycleConfig.mockReset();
    getLifecycleConfig.mockResolvedValue(makeLifecycle());
    updateLifecycleConfig.mockResolvedValue(makeLifecycle());
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

  it('carries a newly selected flowering_strategy value into the submit payload', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LifecycleConfigSection speciesKey="sp-1" />, {
      store: createStoreWithExpertise('expert'),
    });

    const fs = within(await screen.findByTestId('form-field-flowering_strategy')).getByRole(
      'combobox',
    );
    await user.click(fs);
    await user.click(
      await screen.findByRole('option', { name: i18n.t('enums.floweringStrategy.monocarpic') }),
    );
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateLifecycleConfig).toHaveBeenCalled());
    expect(updateLifecycleConfig).toHaveBeenCalledWith(
      'sp-1',
      'lc-1',
      expect.objectContaining({ flowering_strategy: 'monocarpic' }),
    );
  });

  it('normalises a cleared optional lifecycle select to null on submit', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LifecycleConfigSection speciesKey="sp-1" />, {
      store: createStoreWithExpertise('expert'),
    });

    // The mock starts with cultivation_cycle_type = 'annual'; clearing it to the
    // empty option must serialise as null (not '') in the update payload.
    const cct = within(await screen.findByTestId('form-field-cultivation_cycle_type')).getByRole(
      'combobox',
    );
    await user.click(cct);
    await user.click(await screen.findByRole('option', { name: '—' }));
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateLifecycleConfig).toHaveBeenCalled());
    expect(updateLifecycleConfig).toHaveBeenCalledWith(
      'sp-1',
      'lc-1',
      expect.objectContaining({ cultivation_cycle_type: null }),
    );
  });
});
