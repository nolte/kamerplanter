import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import HarvestCreateDialog from '@/pages/ernte/HarvestCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const CREATE_URL = '/api/v1/t/:tenant/harvest/plants/:plantKey/batches';

function duplicateResponse() {
  return HttpResponse.json(
    {
      error_id: 'err_dup',
      error_code: 'DUPLICATE_ENTRY',
      message: "harvest_batches with batch_id='HARVEST-2026-001' already exists.",
      details: [
        {
          field: 'batch_id',
          reason: "Value 'HARVEST-2026-001' is already taken.",
          code: 'DUPLICATE_ENTRY',
        },
      ],
      timestamp: '',
      path: '',
      method: 'POST',
    },
    { status: 409 },
  );
}

describe('HarvestCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
  });

  it('surfaces a duplicate 409 as a snackbar AND a batch-id field error', async () => {
    server.use(http.post(CREATE_URL, () => duplicateResponse()));
    const user = userEvent.setup();
    renderWithProviders(
      <HarvestCreateDialog
        open
        onClose={vi.fn()}
        onCreated={vi.fn()}
        plantKey="plant-1"
      />,
    );

    // Enter an explicit batch id that will collide, then submit.
    const batchField = await screen.findByTestId('form-field-batch_id');
    await user.type(
      batchField.querySelector('input') as HTMLInputElement,
      'HARVEST-2026-001',
    );
    await user.click(await screen.findByTestId('form-submit-button'));

    // Snackbar: the duplicate-specific message (root-cause fix — no longer silent).
    expect(
      await screen.findByText(i18n.t('errors.duplicate')),
    ).toBeTruthy();

    // Field-level hint on the batch_id input (localised).
    expect(
      await screen.findByText(i18n.t('pages.harvest.batchIdDuplicate')),
    ).toBeTruthy();
  });

  it('does not close the dialog and re-enables submit after a duplicate error', async () => {
    const onCreated = vi.fn();
    server.use(http.post(CREATE_URL, () => duplicateResponse()));
    const user = userEvent.setup();
    renderWithProviders(
      <HarvestCreateDialog
        open
        onClose={vi.fn()}
        onCreated={onCreated}
        plantKey="plant-1"
      />,
    );

    await user.click(await screen.findByTestId('form-submit-button'));

    await waitFor(() =>
      expect(
        screen.getByTestId('form-submit-button').hasAttribute('disabled'),
      ).toBe(false),
    );
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('creates the batch and reports success on the happy path', async () => {
    const onCreated = vi.fn();
    server.use(
      http.post(CREATE_URL, () =>
        HttpResponse.json(
          {
            key: 'hb-1',
            batch_id: 'HARVEST-20260724-plant-1',
            plant_key: 'plant-1',
            harvest_date: null,
            harvest_type: 'final',
            wet_weight_g: null,
            estimated_dry_weight_g: null,
            actual_dry_weight_g: null,
            quality_grade: null,
            harvester: '',
            notes: null,
            created_at: null,
            updated_at: null,
          },
          { status: 201 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(
      <HarvestCreateDialog
        open
        onClose={vi.fn()}
        onCreated={onCreated}
        plantKey="plant-1"
      />,
    );

    await user.click(await screen.findByTestId('form-submit-button'));

    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    expect(await screen.findByText(i18n.t('pages.harvest.created'))).toBeTruthy();
  });
});
