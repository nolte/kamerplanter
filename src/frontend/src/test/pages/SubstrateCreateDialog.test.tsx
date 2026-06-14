import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SubstrateCreateDialog from '@/pages/standorte/SubstrateCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('SubstrateCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the dialog with its title and chemistry fields when open', async () => {
    renderWithProviders(<SubstrateCreateDialog open onClose={() => {}} onCreated={() => {}} />);
    expect(await screen.findByTestId('substrate-create-dialog')).toBeTruthy();
    expect(screen.getByTestId('form-field-ph_base')).toBeTruthy();
    expect(screen.getByTestId('form-field-ec_base_ms')).toBeTruthy();
  });

  it('submits the prefilled defaults and calls onCreated', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SubstrateCreateDialog open onClose={() => {}} onCreated={onCreated} />);

    await screen.findByTestId('substrate-create-dialog');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
  });

  it('surfaces a server error without calling onCreated', async () => {
    server.use(
      http.post('/api/v1/substrates', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SubstrateCreateDialog open onClose={() => {}} onCreated={onCreated} />);

    await screen.findByTestId('substrate-create-dialog');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('form-submit-button')).not.toBeDisabled();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('lets the user enter a brand name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateCreateDialog open onClose={() => {}} onCreated={() => {}} />);

    const brandField = within(await screen.findByTestId('form-field-brand')).getByRole('textbox');
    await user.type(brandField, 'Acme');
    expect(brandField).toHaveValue('Acme');
  });

  it('calls onClose when cancelled', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(<SubstrateCreateDialog open onClose={onClose} onCreated={() => {}} />);
    await user.click(await screen.findByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
