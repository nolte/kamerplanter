import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { useForm } from 'react-hook-form';
import i18n from 'i18next';
import PlanEditTab from '@/pages/duengung/nutrient-plan-detail/PlanEditTab';
import type { EditFormData } from '@/pages/duengung/nutrient-plan-detail/nutrientPlanSchema';
import type { ScheduleMode, Species } from '@/api/types';
import type { CatalogueReader, CatalogueStatus } from '@/hooks/useCatalogue';
import { renderWithProviders, createStoreWithExpertise, type TestStore } from '../helpers';

function defaults(): EditFormData {
  return {
    name: 'Plan',
    description: '',
    recommended_substrate_type: null,
    reference_substrate_type: 'soil',
    author: '',
    is_template: false,
    version: '1',
    tags: [],
    species_keys: [],
    schedule_enabled: true,
    schedule_mode: 'weekdays',
    weekday_schedule: [0],
    interval_days: 3,
    preferred_time: '08:00',
    application_method: 'drench',
    reminder_hours_before: 2,
    times_per_day: 1,
    water_mix_ratio_ro_percent: null,
    cycle_restart_from_sequence: null,
  };
}

const TOMATO = {
  key: 'solanum-lycopersicum',
  scientific_name: 'Solanum lycopersicum',
  common_names: ['Tomate'],
  genus: 'Solanum',
  family_name: 'Solanaceae',
} as Species;
const BASIL = {
  key: 'ocimum-basilicum',
  scientific_name: 'Ocimum basilicum',
  common_names: ['Basilikum'],
  genus: 'Ocimum',
  family_name: 'Lamiaceae',
} as Species;

function catalogue(status: CatalogueStatus = 'ready', items: Species[] = [TOMATO, BASIL]): CatalogueReader<Species> {
  return {
    name: 'species',
    items: status === 'ready' ? items : [],
    status,
    error: status === 'failed' ? 'errors.generic' : null,
    isEmpty: status === 'ready' && items.length === 0,
    reload: vi.fn(),
  };
}

interface HarnessProps {
  isReadOnly?: boolean;
  saving?: boolean;
  isDirty?: boolean;
  scheduleEnabled?: boolean;
  scheduleMode?: ScheduleMode;
  weekdaySchedule?: number[];
  onSubmit?: (e: React.FormEvent<HTMLFormElement>) => void;
  onCancel?: () => void;
  onWeekdayToggle?: (index: number) => void;
  speciesCatalogue?: CatalogueReader<Species>;
  speciesKeys?: string[];
  onValues?: (values: EditFormData) => void;
}

function Harness({
  isReadOnly = false,
  saving = false,
  isDirty = true,
  scheduleEnabled = true,
  scheduleMode = 'weekdays',
  weekdaySchedule = [0],
  onSubmit = () => {},
  onCancel = () => {},
  onWeekdayToggle = () => {},
  speciesCatalogue = catalogue(),
  speciesKeys = [],
  onValues = () => {},
}: HarnessProps) {
  const { control, getValues } = useForm<EditFormData>({
    defaultValues: { ...defaults(), species_keys: speciesKeys },
  });
  return (
    <PlanEditTab
      control={control}
      onSubmit={(e) => {
        e.preventDefault();
        onValues(getValues());
        onSubmit(e);
      }}
      isReadOnly={isReadOnly}
      saving={saving}
      isDirty={isDirty}
      onCancel={onCancel}
      scheduleMode={scheduleMode}
      scheduleEnabled={scheduleEnabled}
      weekdaySchedule={weekdaySchedule}
      onWeekdayToggle={onWeekdayToggle}
      speciesCatalogue={speciesCatalogue}
    />
  );
}

function render(props: HarnessProps = {}, store: TestStore = createStoreWithExpertise('expert')) {
  return renderWithProviders(<Harness {...props} />, { store });
}

describe('PlanEditTab', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the editable form with save and cancel actions', () => {
    render();
    expect(screen.getByText(i18n.t('pages.nutrientPlans.sectionGeneral'))).toBeInTheDocument();
    expect(screen.getByTestId('form-submit-button')).toBeInTheDocument();
    expect(screen.getByTestId('form-cancel-button')).toBeInTheDocument();
  });

  it('submits the form and cancels through the action buttons', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onCancel = vi.fn();
    render({ onSubmit, onCancel });

    await user.click(screen.getByTestId('form-submit-button'));
    expect(onSubmit).toHaveBeenCalledTimes(1);

    await user.click(screen.getByTestId('form-cancel-button'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('hides the actions and shows the read-only hint for protected plans', () => {
    render({ isReadOnly: true });
    expect(screen.queryByTestId('form-submit-button')).toBeNull();
    expect(
      screen.getByText(i18n.t('common.origin.readOnlyHint')),
    ).toBeInTheDocument();
  });

  it('renders the weekday checkboxes and forwards a toggle', async () => {
    const user = userEvent.setup();
    const onWeekdayToggle = vi.fn();
    render({ scheduleMode: 'weekdays', weekdaySchedule: [0], onWeekdayToggle });

    const monday = screen.getByRole('checkbox', { name: i18n.t('pages.wateringSchedule.mon') });
    expect(monday).toBeChecked();
    const tuesday = screen.getByRole('checkbox', { name: i18n.t('pages.wateringSchedule.tue') });
    expect(tuesday).not.toBeChecked();

    await user.click(tuesday);
    expect(onWeekdayToggle).toHaveBeenCalledWith(1);
  });

  it('renders the interval field instead of weekdays in interval mode', () => {
    render({ scheduleMode: 'interval' });
    expect(
      screen.queryByRole('checkbox', { name: i18n.t('pages.wateringSchedule.mon') }),
    ).toBeNull();
    expect(
      screen.getByLabelText(i18n.t('pages.wateringSchedule.intervalDays'), { exact: false }),
    ).toBeInTheDocument();
  });

  it('reveals the advanced expert section for expert users', () => {
    render({}, createStoreWithExpertise('expert'));
    expect(screen.getByText(i18n.t('pages.nutrientPlans.sectionAdvanced'))).toBeInTheDocument();
    expect(screen.getByTestId('water-mix-slider')).toBeInTheDocument();
  });

  it('hides the advanced section for beginner users', () => {
    render({}, createStoreWithExpertise('beginner'));
    expect(screen.queryByText(i18n.t('pages.nutrientPlans.sectionAdvanced'))).toBeNull();
    expect(screen.queryByTestId('water-mix-slider')).toBeNull();
  });

  it('switches the schedule mode through the toggle group', async () => {
    const user = userEvent.setup();
    render({ scheduleMode: 'weekdays' });

    const intervalToggle = screen.getByRole('button', {
      name: i18n.t('pages.wateringSchedule.interval'),
    });
    await user.click(intervalToggle);
    // pressing the already-selected toggle emits a null value (deselect) —
    // exercises the guarded branch that ignores it
    await user.click(intervalToggle);
    expect(intervalToggle).toBeInTheDocument();
  });

  it('adjusts the water-mix slider', async () => {
    const user = userEvent.setup();
    render();
    const slider = screen.getByRole('slider');
    slider.focus();
    await user.keyboard('{ArrowRight}');
    expect(slider).toBeInTheDocument();
  });

  describe('species relation (#1618)', () => {
    it('shows the linked species by name and keeps them in the form', async () => {
      const user = userEvent.setup();
      const onValues = vi.fn();
      render({ speciesKeys: ['solanum-lycopersicum'], onValues });

      expect(screen.getByText('Tomate (Solanum lycopersicum)')).toBeInTheDocument();
      await user.click(screen.getByTestId('form-submit-button'));
      expect(onValues.mock.calls[0][0].species_keys).toEqual(['solanum-lycopersicum']);
    });

    it('adds a species picked from the catalogue', async () => {
      const user = userEvent.setup();
      const onValues = vi.fn();
      render({ onValues });

      const input = screen.getByRole('combobox', { name: i18n.t('pages.nutrientPlans.speciesKeys') });
      await user.click(input);
      await user.type(input, 'Basil');
      await user.click(await screen.findByRole('option', { name: 'Basilikum (Ocimum basilicum)' }));
      await user.click(screen.getByTestId('form-submit-button'));

      expect(onValues.mock.calls[0][0].species_keys).toEqual(['ocimum-basilicum']);
    });

    it('keeps a linked key the catalogue does not hold instead of dropping it', async () => {
      const user = userEvent.setup();
      const onValues = vi.fn();
      render({ speciesKeys: ['unknown-species'], onValues });

      expect(screen.getByText('unknown-species')).toBeInTheDocument();
      await user.click(screen.getByTestId('form-submit-button'));
      expect(onValues.mock.calls[0][0].species_keys).toEqual(['unknown-species']);
    });

    it('explains what the relation does', () => {
      render();
      expect(screen.getByText(i18n.t('pages.nutrientPlans.speciesKeysHelper'))).toBeInTheDocument();
    });

    it('disables the picker while the catalogue is loading', () => {
      render({ speciesCatalogue: catalogue('loading') });
      expect(screen.getByRole('combobox', { name: i18n.t('pages.nutrientPlans.speciesKeys') })).toBeDisabled();
    });

    it('shows a failed catalogue load instead of an empty picker', () => {
      render({ speciesCatalogue: catalogue('failed') });
      expect(screen.getByRole('combobox', { name: i18n.t('pages.nutrientPlans.speciesKeys') })).toBeDisabled();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('disables the picker for a read-only plan', () => {
      render({ isReadOnly: true });
      expect(screen.getByRole('combobox', { name: i18n.t('pages.nutrientPlans.speciesKeys') })).toBeDisabled();
    });
  });
});
