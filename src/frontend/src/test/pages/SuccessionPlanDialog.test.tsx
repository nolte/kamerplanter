import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import SuccessionPlanDialog from '@/pages/durchlaeufe/SuccessionPlanDialog';
import { renderWithProviders } from '../helpers';
import type { SuccessionPlan } from '@/api/types';

const existingPlan: SuccessionPlan = {
  key: 'sp-1',
  name: 'Salat Staffelanbau',
  species_key: 'sp-1',
  cultivar_key: null,
  interval_days: 21,
  start_date: '2024-04-01',
  end_date: '2024-09-01',
  plants_per_batch: 6,
  total_batches: 8,
  completed_batches: 2,
  status: 'active',
  reminder_days_before: 3,
  location_key: null,
  notes: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

describe('SuccessionPlanDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the create title and the batch preview', async () => {
    renderWithProviders(
      <SuccessionPlanDialog open onClose={() => {}} onSaved={() => {}} />,
    );
    expect(await screen.findByText('Staffelanbau anlegen')).toBeTruthy();
    // Preview alert is always shown; with equal start/end and interval 21 => 1 batch
    const preview = screen.getByTestId('batch-preview');
    expect(within(preview).getByText(/1 Staffeln/)).toBeTruthy();
  });

  it('shows an edit title and locks the species field in edit mode', async () => {
    renderWithProviders(
      <SuccessionPlanDialog open plan={existingPlan} onClose={() => {}} onSaved={() => {}} />,
    );
    expect(await screen.findByText('Staffelanbau bearbeiten')).toBeTruthy();
    const speciesInput = screen.getByTestId('form-field-species_key').querySelector('input');
    expect(speciesInput?.disabled).toBe(true);
  });

  it('creates a plan and calls onSaved', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    renderWithProviders(
      <SuccessionPlanDialog open onClose={() => {}} onSaved={onSaved} />,
    );

    await user.type(
      screen.getByTestId('form-field-name').querySelector('input')!,
      'Neuer Staffelplan',
    );

    // Pick a species from the autocomplete (mockSpecies has "Tomato").
    const speciesInput = screen
      .getByTestId('form-field-species_key')
      .querySelector('input')!;
    await user.click(speciesInput);
    await user.type(speciesInput, 'Tom');
    const option = await screen.findByText('Tomato');
    await user.click(option);

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onSaved).toHaveBeenCalled();
    });
  });

  it('blocks submission when the end date is before the start date', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    renderWithProviders(
      <SuccessionPlanDialog open onClose={() => {}} onSaved={onSaved} />,
    );

    await user.type(
      screen.getByTestId('form-field-name').querySelector('input')!,
      'Ungueltiger Plan',
    );

    const speciesInput = screen
      .getByTestId('form-field-species_key')
      .querySelector('input')!;
    await user.click(speciesInput);
    await user.type(speciesInput, 'Tom');
    await user.click(await screen.findByText('Tomato'));

    // Set an end date before the start date (start defaults to today).
    // FormDateField has no testid, so locate it by its label.
    const endField = screen.getByLabelText(/Ende/) as HTMLInputElement;
    await user.clear(endField);
    await user.type(endField, '2000-01-01');

    await waitFor(() => {
      expect(screen.getByTestId('batch-preview').textContent).toMatch(
        /Ende muss am oder nach dem Beginn/i,
      );
    });

    await user.click(screen.getByTestId('form-submit-button'));
    expect(onSaved).not.toHaveBeenCalled();
  });
});
