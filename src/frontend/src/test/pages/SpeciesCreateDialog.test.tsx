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
