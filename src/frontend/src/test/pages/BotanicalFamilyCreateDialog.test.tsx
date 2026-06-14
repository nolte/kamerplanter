import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import BotanicalFamilyCreateDialog from '@/pages/stammdaten/BotanicalFamilyCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('BotanicalFamilyCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the dialog title and required name field when open', async () => {
    renderWithProviders(
      <BotanicalFamilyCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );
    expect(await screen.findByTestId('botanical-family-create-dialog')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('does not render dialog content when closed', () => {
    renderWithProviders(
      <BotanicalFamilyCreateDialog open={false} onClose={() => {}} onCreated={() => {}} />,
    );
    expect(screen.queryByTestId('botanical-family-create-dialog')).toBeNull();
  });

  it('invokes onClose when the cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(
      <BotanicalFamilyCreateDialog open onClose={onClose} onCreated={() => {}} />,
    );

    await user.click(await screen.findByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('blocks submission and keeps the dialog open when the name does not end in -aceae', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <BotanicalFamilyCreateDialog open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Invalidname');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByText(/Muss auf '-aceae' enden/)).toBeTruthy();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('submits a valid family and calls onCreated', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <BotanicalFamilyCreateDialog open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Rosaceae');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
  });

  it('surfaces a server error without calling onCreated', async () => {
    server.use(
      http.post('/api/v1/botanical-families', () =>
        HttpResponse.json(
          { error_id: 'e1', error_code: 'CONFLICT', message: 'exists', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <BotanicalFamilyCreateDialog open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Rosaceae');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('form-submit-button')).not.toBeDisabled();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });
});
