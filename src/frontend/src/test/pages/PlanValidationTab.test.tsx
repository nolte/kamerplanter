import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import PlanValidationTab from '@/pages/duengung/nutrient-plan-detail/PlanValidationTab';
import type {
  PlanValidationResult,
  NutrientPlanPhaseEntry,
  DeliveryChannel,
} from '@/api/types';
import { renderWithProviders } from '../helpers';

function makeChannel(overrides: Partial<DeliveryChannel> = {}): DeliveryChannel {
  return {
    channel_id: 'c1',
    label: 'Channel One',
    application_method: 'drench',
    enabled: true,
    notes: null,
    schedule: null,
    target_ec_ms: 1.2,
    target_ph: 6,
    fertilizer_dosages: [],
    method_params: null,
    ...overrides,
  } as DeliveryChannel;
}

function makeEntry(): NutrientPlanPhaseEntry {
  return {
    key: 'e1',
    plan_key: 'np-1',
    phase_name: 'vegetative',
    sequence_order: 1,
    week_start: 1,
    week_end: 4,
    is_recurring: false,
    npk_ratio: [3, 1, 2],
    calcium_ppm: null,
    magnesium_ppm: null,
    target_ec_ms: 1.2,
    reference_ec_ms: null,
    target_calcium_ppm: null,
    target_magnesium_ppm: null,
    reference_base_ec: 0.3,
    notes: null,
    delivery_channels: [makeChannel()],
    watering_schedule_override: null,
    water_mix_ratio_ro_percent: null,
    created_at: null,
    updated_at: null,
  };
}

describe('PlanValidationTab', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('shows a spinner while validating with no result yet', () => {
    renderWithProviders(
      <PlanValidationTab validation={null} validating entries={[]} onEditChannel={vi.fn()} />,
    );
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders nothing meaningful when idle and empty', () => {
    renderWithProviders(
      <PlanValidationTab validation={null} validating={false} entries={[]} onEditChannel={vi.fn()} />,
    );
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(screen.queryByText(i18n.t('pages.nutrientPlans.completeness'))).toBeNull();
  });

  it('reports an incomplete plan with its issues', () => {
    const validation: PlanValidationResult = {
      completeness: { complete: false, issues: ['Missing flowering phase', 'No EC target'] },
      channel_validations: [],
      valid: false,
    };
    renderWithProviders(
      <PlanValidationTab validation={validation} validating={false} entries={[]} onEditChannel={vi.fn()} />,
    );
    expect(screen.getByText(i18n.t('pages.nutrientPlans.planIncomplete'))).toBeInTheDocument();
    expect(screen.getByText('Missing flowering phase')).toBeInTheDocument();
    expect(screen.getByText('No EC target')).toBeInTheDocument();
  });

  it('reports a complete plan and channel validation results with an EC budget', async () => {
    const user = userEvent.setup();
    const onEditChannel = vi.fn();
    const validation: PlanValidationResult = {
      completeness: { complete: true, issues: [] },
      channel_validations: [
        {
          entry_key: 'e1',
          phase_name: 'vegetative',
          valid: false,
          channel_results: [
            {
              channel_id: 'c1',
              label: 'Channel One',
              issues: ['EC too high'],
              ec_budget: { target: 1.5, calculated: 1.82, delta: 0.32, tolerance: 0.2 },
            },
            {
              channel_id: 'c1',
              label: '',
              issues: [],
              ec_budget: null,
            },
          ],
        },
      ],
      valid: false,
    };
    renderWithProviders(
      <PlanValidationTab
        validation={validation}
        validating={false}
        entries={[makeEntry()]}
        onEditChannel={onEditChannel}
      />,
    );

    expect(screen.getByText(i18n.t('pages.nutrientPlans.planComplete'))).toBeInTheDocument();
    expect(screen.getByText(/EC too high/)).toBeInTheDocument();
    expect(screen.getByText(/1\.82 \/ 1\.5/)).toBeInTheDocument();
    // channel with no issues renders the "no issues" label
    expect(
      screen.getByText(i18n.t('pages.deliveryChannels.validation.noIssues'), { exact: false }),
    ).toBeInTheDocument();

    await user.click(screen.getAllByTestId('EditIcon')[0].closest('button')!);
    expect(onEditChannel).toHaveBeenCalledWith('e1', expect.objectContaining({ channel_id: 'c1' }));
  });

  it('ignores an edit click when the entry cannot be resolved', async () => {
    const user = userEvent.setup();
    const onEditChannel = vi.fn();
    const validation: PlanValidationResult = {
      completeness: { complete: true, issues: [] },
      channel_validations: [
        {
          entry_key: 'ghost',
          phase_name: 'vegetative',
          valid: true,
          channel_results: [{ channel_id: 'c1', label: 'X', issues: ['bad'], ec_budget: null }],
        },
      ],
      valid: true,
    };
    renderWithProviders(
      <PlanValidationTab
        validation={validation}
        validating={false}
        entries={[makeEntry()]}
        onEditChannel={onEditChannel}
      />,
    );
    await user.click(screen.getAllByTestId('EditIcon')[0].closest('button')!);
    expect(onEditChannel).not.toHaveBeenCalled();
  });

  it('ignores an edit click when the channel is missing from the entry', async () => {
    const user = userEvent.setup();
    const onEditChannel = vi.fn();
    const validation: PlanValidationResult = {
      completeness: { complete: true, issues: [] },
      channel_validations: [
        {
          entry_key: 'e1',
          phase_name: 'vegetative',
          valid: true,
          channel_results: [
            {
              channel_id: 'unknown',
              label: 'X',
              issues: [],
              ec_budget: { target: 1, calculated: 1, delta: -0.1, tolerance: 0.2 },
            },
          ],
        },
      ],
      valid: true,
    };
    renderWithProviders(
      <PlanValidationTab
        validation={validation}
        validating={false}
        entries={[makeEntry()]}
        onEditChannel={onEditChannel}
      />,
    );
    await user.click(screen.getAllByTestId('EditIcon')[0].closest('button')!);
    expect(onEditChannel).not.toHaveBeenCalled();
  });
});
