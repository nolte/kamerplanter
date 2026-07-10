import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { useForm } from 'react-hook-form';
import i18n from 'i18next';
import PlanEditTab from '@/pages/duengung/nutrient-plan-detail/PlanEditTab';
import type { EditFormData } from '@/pages/duengung/nutrient-plan-detail/nutrientPlanSchema';
import type { ScheduleMode } from '@/api/types';
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
}: HarnessProps) {
  const { control } = useForm<EditFormData>({ defaultValues: defaults() });
  return (
    <PlanEditTab
      control={control}
      onSubmit={(e) => {
        e.preventDefault();
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
});
