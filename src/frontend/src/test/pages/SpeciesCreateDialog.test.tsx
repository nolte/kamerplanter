import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SpeciesCreateDialog from '@/pages/stammdaten/SpeciesCreateDialog';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';
import { server } from '../mocks/server';

describe('SpeciesCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the dialog with its title when open', async () => {
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(await screen.findByTestId('species-create-dialog')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('hides expert-only fields for a beginner and reveals them via the show-all toggle', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('beginner'),
    });

    // scientific_name is intermediate → not visible to a beginner
    await screen.findByTestId('species-create-dialog');
    expect(screen.queryByTestId('form-field-scientific_name')).toBeNull();

    // Toggling "show all fields" reveals the gated fields
    await user.click(screen.getByTestId('show-all-fields-toggle'));
    await waitFor(() => {
      expect(screen.getByTestId('form-field-scientific_name')).toBeTruthy();
    });
  });

  it('shows the scientific-name field directly for an expert', async () => {
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(await screen.findByTestId('form-field-scientific_name')).toBeTruthy();
    // Expert level does not render the show-all toggle
    expect(screen.queryByTestId('show-all-fields-toggle')).toBeNull();
  });

  it('loads families into the family select when opened', async () => {
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });
    // Family options come from the mocked /botanical-families endpoint
    await waitFor(() => {
      expect(screen.getByTestId('form-field-family_key')).toBeTruthy();
    });
  });

  it('submits a valid species and calls onCreated', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-scientific_name')).getByRole('textbox');
    await user.type(nameField, 'Ocimum basilicum');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
  });

  it('offers all 12 growth-habit options', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });

    const combobox = within(await screen.findByTestId('form-field-growth_habit')).getByRole(
      'combobox',
    );
    await user.click(combobox);
    const listbox = await screen.findByRole('listbox');
    expect(within(listbox).getAllByRole('option')).toHaveLength(12);
    // Spot-check the previously-missing resolver-critical values are now present.
    for (const value of ['fern', 'bulb_geophyte', 'epiphyte', 'succulent']) {
      expect(
        within(listbox).getByText(i18n.t(`enums.growthHabit.${value}`)),
      ).toBeTruthy();
    }
  });

  it('carries a selected growth_habit and photosynthesis_type into the submit payload', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/species', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          { key: 'sp-new', ...captured, created_at: new Date().toISOString(), updated_at: null },
          { status: 201 },
        );
      }),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-scientific_name')).getByRole(
      'textbox',
    );
    await user.type(nameField, 'Sempervivum tectorum');

    // growth_habit → succulent (a value not in the legacy 5-option list)
    const habitBox = within(screen.getByTestId('form-field-growth_habit')).getByRole('combobox');
    await user.click(habitBox);
    await user.click(
      await screen.findByRole('option', { name: i18n.t('enums.growthHabit.succulent') }),
    );

    // photosynthesis_type → CAM
    const photoBox = within(screen.getByTestId('form-field-photosynthesis_type')).getByRole(
      'combobox',
    );
    await user.click(photoBox);
    await user.click(
      await screen.findByRole('option', { name: i18n.t('enums.photosynthesisType.cam') }),
    );

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(captured).toMatchObject({ growth_habit: 'succulent', photosynthesis_type: 'cam' });
  });

  it('normalises an unset photosynthesis_type to null in the submit payload', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/species', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          { key: 'sp-new', ...captured, created_at: new Date().toISOString(), updated_at: null },
          { status: 201 },
        );
      }),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-scientific_name')).getByRole(
      'textbox',
    );
    await user.type(nameField, 'Ocimum basilicum');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(captured).toMatchObject({ photosynthesis_type: null });
  });

  it('keeps the dialog open and does not call onCreated on a server error', async () => {
    server.use(
      http.post('/api/v1/species', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SpeciesCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-scientific_name')).getByRole('textbox');
    await user.type(nameField, 'Ocimum basilicum');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('form-submit-button')).not.toBeDisabled();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('resets show-all state and calls onClose when cancelled', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(<SpeciesCreateDialog open onClose={onClose} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });

    await user.click(await screen.findByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
